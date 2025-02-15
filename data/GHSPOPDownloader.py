import shutil
import geopandas as gpd
from shutil import rmtree
from shapely.geometry import Point
import requests
import zipfile
import os
import osmnx as ox
import numpy as np
import rasterio
import rasterio.mask
from rasterio.io import MemoryFile
from rasterio.merge import merge
from shapely.geometry import box

ox.settings.use_cache = False

class GHSPOPDownloader:
    shapefile_path = "../tiling_schema/WGS84_tile_schema.shp"

    def __init__(self, address, extracted_dir="extracted_files"):
        self.address = address
        self.extracted_dir = extracted_dir
        self.lat, self.lon = self.__geocode_address()

    def __geocode_address(self):
        location = ox.geocode(self.address)
        return location[1], location[0]

    def __remove_existing_directory(self):
        if os.path.exists(self.extracted_dir):
            rmtree(self.extracted_dir)

    def __load_shapefile(self):
        tiles_gdf = gpd.read_file(self.shapefile_path)
        if tiles_gdf.crs != "EPSG:4326":
            tiles_gdf = tiles_gdf.to_crs("EPSG:4326")
        return tiles_gdf

    def __create_point_gdf(self):
        point = Point(self.lat, self.lon)
        return gpd.GeoDataFrame([{'geometry': point}], crs="EPSG:4326")

    def __get_tile_id(self, tiles_gdf, point_gdf):
        current_tile = tiles_gdf[tiles_gdf.contains(point_gdf.geometry.iloc[0])]
        if not current_tile.empty:
            return current_tile.iloc[0]['tile_id']
        return None

    def __download_tile(self, tile_id):
        url = f"https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_POP_GLOBE_R2023A/GHS_POP_E2025_GLOBE_R2023A_4326_3ss/V1-0/tiles/GHS_POP_E2025_GLOBE_R2023A_4326_3ss_V1_0_{tile_id}.zip"
        response = requests.get(url)
        if response.status_code == 200:
            zip_path = 'tile_download.zip'
            with open(zip_path, 'wb') as file:
                file.write(response.content)
            return zip_path
        return None

    def __extract_tif_file(self, zip_path):
        """
        Extract TIF file from zip archive.
        Files will be kept until explicitly cleaned up later.
        """
        tif_path = None
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for file in zip_ref.namelist():
                    if file.endswith('.tif'):
                        zip_ref.extract(file, self.extracted_dir)
                        tif_path = os.path.join(self.extracted_dir, file)
                        if not os.path.exists(tif_path):
                            tif_path = None
                        break

            # Remove only the zip file after successful extraction
            if os.path.exists(zip_path):
                os.remove(zip_path)

            return tif_path

        except Exception as e:
            print(f"Error during TIF extraction: {str(e)}")
            return None

    def __get_tiles_for_bounds(self, bounds, tiles_gdf):
        bbox = box(bounds.min_x, bounds.min_y, bounds.max_x, bounds.max_y)

        bbox_gdf = gpd.GeoDataFrame([{'geometry': bbox}], crs="EPSG:4326")

        # Get the tiles in the bounding box
        intersecting_tiles = tiles_gdf[tiles_gdf.intersects(bbox_gdf.geometry[0])]

        # Get the tile_id
        tile_ids = []
        for _, row in intersecting_tiles.iterrows():
            tile_id = row['tile_id']
            if tile_id:
                tile_ids.append(tile_id)

        return tile_ids

    def __cleanup_files(self, file_paths):
        """
        Clean up processed files and directories.
        """
        for path in file_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                print(f"Error removing file {path}: {str(e)}")

        try:
            if os.path.exists(self.extracted_dir) and not os.listdir(self.extracted_dir):
                shutil.rmtree(self.extracted_dir)
        except Exception as e:
            print(f"Error removing directory {self.extracted_dir}: {str(e)}")

    def __merge_tiles(self, tiles):
        """
        Merge multiple GHS-POP tiles into a single raster.
        """
        # Create temporary datasets for merging
        temp_datasets = []
        for data, transform, crs, shape in tiles:
            profile = {
                'driver': 'GTiff',
                'height': shape[0],
                'width': shape[1],
                'count': 1,
                'dtype': data.dtype,
                'crs': crs,
                'transform': transform
            }
            temp_datasets.append(rasterio.io.MemoryFile().open(**profile))
            temp_datasets[-1].write(data, 1)

        # Merge datasets
        merged_data, merged_transform = merge(temp_datasets)

        # Clean up temporary datasets
        for dataset in temp_datasets:
            dataset.close()

        return (
            merged_data[0],
            merged_transform,
            tiles[0][2],
            merged_data.shape[1:]
        )
    def __process_single_tile(self, tile_id):
        """
        Process a single GHS-POP tile.
        """
        try:
            # Download tile
            zip_path = self.__download_tile(tile_id)
            if not zip_path:
                print(f"Failed to download tile {tile_id}")
                return None

            # Extract TIF file
            tif_path = self.__extract_tif_file(zip_path)
            if tif_path is None:
                print(f"Failed to extract TIF file from {zip_path}")
                return None

            with rasterio.open(tif_path) as dataset:
                data = dataset.read(1)
                return data, dataset.transform, dataset.crs, dataset.shape

        except Exception as e:
            print(f"Error processing tile {tile_id}: {str(e)}")
            return None

    def __download_and_process_tiles(self, tile_ids):
        """
        Download and process GHS-POP tiles based on the provided tile IDs.
        """
        if not tile_ids:
            raise ValueError("No tile IDs provided for download.")

        downloaded_tiles = []
        processed_paths = []

        try:
            for tile_id in tile_ids:
                tile_data = self.__process_single_tile(tile_id)
                if tile_data:
                    downloaded_tiles.append(tile_data)
                    processed_paths.append(os.path.join(self.extracted_dir,f"GHS_POP_{tile_id}.tif"))

            if not downloaded_tiles:
                raise ValueError("Failed to download any valid tiles.")

            # Handle the number of tiles downloaded
            if len(downloaded_tiles) == 1:
                result = downloaded_tiles[0]
            else:
                result = self.__merge_tiles(downloaded_tiles)

            return result

        finally:
            self.__cleanup_files(processed_paths)

    def __crop_bounds(self, data, transform, bounds):
        """
        Crop the given data to the specified bounding box.
        """
        crs = "EPSG:4326"
        bbox = box(bounds.min_x, bounds.min_y, bounds.max_x, bounds.max_y)
        geo = gpd.GeoDataFrame({'geometry': [bbox]}, crs=crs)
        geo = geo.to_crs(crs=rasterio.crs.CRS.from_string(crs))

        # Memoryfile used to store the cropped raster temporarily
        with MemoryFile() as memfile:
            with memfile.open(
                    driver="GTiff",
                    height=data.shape[0],
                    width=data.shape[1],
                    count=1,
                    dtype=data.dtype,
                    crs=crs,
                    transform=transform,
            ) as dataset:
                dataset.write(data, 1)

                # Make the crop using rasterio.mask
                out_image, out_transform = rasterio.mask.mask(
                    dataset, geo.geometry, crop=True
                )

        return out_image, out_transform, crs, out_image.shape

    def get_population_area(self, bounding_box):
        """
        Download and process GHS-POP data for the given bounding box, converting it to EPSG:4326.
        """
        self.__remove_existing_directory()

        tiles_gdf = self.__load_shapefile()

        # Get necessary tiles for the area
        tiles_to_download = self.__get_tiles_for_bounds(bounding_box, tiles_gdf)

        if not tiles_to_download:
            raise ValueError("No tiles to download for the given bounds.")

        ghs_data, ghs_transform, ghs_crs, ghs_shape = self.__download_and_process_tiles(tiles_to_download)
        ghs_data_cropped, ghs_transform_cropped, ghs_crs_cropped, ghs_shape_cropped = self.__crop_bounds(ghs_data, ghs_transform, bounding_box)
        ghs_data_cropped = np.squeeze(ghs_data_cropped, axis=0)
        return ghs_data_cropped, ghs_transform_cropped, ghs_crs_cropped, ghs_shape_cropped