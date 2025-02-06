import shutil
from typing import List, Tuple, Optional

import geopandas as gpd
from shutil import rmtree
from shapely.geometry import Point
from shapely.geometry import box
import requests
import zipfile
import os
import osmnx as ox
import numpy as np
import rasterio
import rasterio.mask
from rasterio.io import MemoryFile
from rasterio.merge import merge
from rasterio.warp import reproject, Resampling as RasterioResampling, calculate_default_transform
from rasterio.transform import Affine
from data.BoundingBox import BoundingBox

ox.settings.use_cache = False

class GHSPOPDownloader:
    def __init__(self, address, shapefile_path, extracted_dir="extracted_files"):
        self.address = address
        self.shapefile_path = shapefile_path
        self.extracted_dir = extracted_dir
        self.lat, self.lon = self.geocode_address()

    def geocode_address(self):
        location = ox.geocode(self.address)
        return location[1], location[0]

    def remove_existing_directory(self):
        if os.path.exists(self.extracted_dir):
            rmtree(self.extracted_dir)

    def load_shapefile(self):
        tiles_gdf = gpd.read_file(self.shapefile_path)
        mollweide_proj = "+proj=moll +lon_0=0 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
        if tiles_gdf.crs != mollweide_proj:
            tiles_gdf = tiles_gdf.to_crs(mollweide_proj)
        return tiles_gdf

    def create_point_gdf(self):
        point = Point(self.lat, self.lon)
        return gpd.GeoDataFrame([{'geometry': point}], crs="ESRI:54009")

    def get_tile_id(self, tiles_gdf, point_gdf):
        current_tile = tiles_gdf[tiles_gdf.contains(point_gdf.geometry.iloc[0])]
        if not current_tile.empty:
            return current_tile.iloc[0]['tile_id']
        return None

    def download_tile(self, tile_id):
        url = f"https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_POP_GLOBE_R2023A/GHS_POP_E2025_GLOBE_R2023A_54009_100/V1-0/tiles/GHS_POP_E2025_GLOBE_R2023A_54009_100_V1_0_{tile_id}.zip"
        response = requests.get(url)
        if response.status_code == 200:
            zip_path = 'tile_download.zip'
            with open(zip_path, 'wb') as file:
                file.write(response.content)
            return zip_path
        return None

    def extract_tif_file(self, zip_path):
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

    def get_tiles_for_bounds(self, bounds, tiles_gdf):
        bbox = box(bounds.min_x, bounds.min_y, bounds.max_x, bounds.max_y)

        mollweide_proj = "+proj=moll +lon_0=0 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
        bbox_gdf = gpd.GeoDataFrame([{'geometry': bbox}], crs=mollweide_proj)

        # Get the tiles in the bounding box
        intersecting_tiles = tiles_gdf[tiles_gdf.intersects(bbox_gdf.geometry[0])]

        # Get the tile_id
        tile_ids = []
        for _, row in intersecting_tiles.iterrows():
            tile_id = row['tile_id']
            if tile_id:
                tile_ids.append(tile_id)

        return tile_ids

    def cleanup_files(self, file_paths, ghs_pop):
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
            if os.path.exists(ghs_pop.extracted_dir) and not os.listdir(ghs_pop.extracted_dir):
                shutil.rmtree(ghs_pop.extracted_dir)
        except Exception as e:
            print(f"Error removing directory {ghs_pop.extracted_dir}: {str(e)}")

    def _merge_tiles(self, tiles: List[Tuple[np.ndarray, rasterio.Affine, str, Tuple[int, int]]]) -> Tuple[
        np.ndarray, rasterio.Affine, str, Tuple[int, int]]:
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
    def _process_single_tile(self, tile_id: str, ghs_pop) -> Optional[
        Tuple[np.ndarray, rasterio.Affine, str, Tuple[int, int]]]:
        """
        Process a single GHS-POP tile.
        """
        try:
            # Download tile
            zip_path = ghs_pop.download_tile(tile_id)
            if not zip_path:
                print(f"Failed to download tile {tile_id}")
                return None

            # Extract TIF file
            tif_path = ghs_pop.extract_tif_file(zip_path)
            if tif_path is None:
                print(f"Failed to extract TIF file from {zip_path}")
                return None

            with rasterio.open(tif_path) as dataset:
                data = dataset.read(1)
                return data, dataset.transform, dataset.crs, dataset.shape

        except Exception as e:
            print(f"Error processing tile {tile_id}: {str(e)}")
            return None

    def download_and_process_tiles(self, tile_ids: List[str], ghs_pop) -> Tuple[
        np.ndarray, rasterio.Affine, str, Tuple[int, int]]:
        """
        Download and process GHS-POP tiles based on the provided tile IDs.
        """
        if not tile_ids:
            raise ValueError("No tile IDs provided for download.")

        downloaded_tiles = []
        processed_paths = []

        try:
            for tile_id in tile_ids:
                tile_data = self._process_single_tile(tile_id, ghs_pop)
                if tile_data:
                    downloaded_tiles.append(tile_data)
                    processed_paths.append(os.path.join(ghs_pop.extracted_dir,f"GHS_POP_E2025_GLOBE_R2023A_54009_100_V1_0_{tile_id}.tif"))

            if not downloaded_tiles:
                raise ValueError("Failed to download any valid tiles.")

            # Handle the number of tiles downloaded
            if len(downloaded_tiles) == 1:
                result = downloaded_tiles[0]
            else:
                result = self._merge_tiles(downloaded_tiles)

            return result

        finally:
            self.cleanup_files(processed_paths, ghs_pop)

    def crop_bounds(self, data, transform, bounds, crs="ESRI:54009"):
        """
        Crop the given data to the specified bounding box.
        """
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

        return out_image, out_transform

    def get_population_area(self, bounding_box):
        """
        Download and process GHS-POP data for the given bounding box, converting it to EPSG:4326.
        """
        self.remove_existing_directory()

        # Ensure bounding_box is an instance of BoundingBox
        if not isinstance(bounding_box, BoundingBox):
            raise ValueError("bounding_box must be an instance of BoundingBox")

        bounds = bounding_box.transform_to_esri54009()

        tiles_gdf = self.load_shapefile()

        # Get necessary tiles for the area
        tiles_to_download = self.get_tiles_for_bounds(bounds, tiles_gdf)

        if not tiles_to_download:
            raise ValueError("No tiles to download for the given bounds.")

        ghs_data, ghs_transform, ghs_crs, ghs_shape = self.download_and_process_tiles(tiles_to_download, self)
        ghs_data_cropped, ghs_transform_cropped = self.crop_bounds(ghs_data, ghs_transform, bounds)

        # Estrarre i limiti della bounding box
        left, bottom, right, top = bounds.min_x, bounds.min_y, bounds.max_x, bounds.max_y


        # Calcolare la trasformazione corretta per EPSG:4326
        dst_transform, width, height = calculate_default_transform(
            ghs_crs, "EPSG:4326", ghs_shape[1], ghs_shape[0], left, bottom, right, top
        )

        # Crea un array vuoto per i dati riproiettati
        ghs_data_4326 = np.empty((height, width), dtype=ghs_data_cropped.dtype)

        # Riproietta i dati
        reproject(
            source=ghs_data_cropped,
            destination=ghs_data_4326,
            src_transform=ghs_transform_cropped,
            src_crs=ghs_crs,
            dst_transform=dst_transform,
            dst_crs="EPSG:4326",
            resampling=RasterioResampling.bilinear
        )

        output_tif_path = "ghs_pop_cropped.tif"

        # Salva il raster riproiettato
        with rasterio.open(output_tif_path, 'w', driver='GTiff',
                           height=height, width=width,
                           count=1, dtype=ghs_data_4326.dtype,
                           crs="EPSG:4326", transform=dst_transform) as dst:
            dst.write(ghs_data_4326, 1)

        return ghs_data_4326, dst_transform, "EPSG:4326", (height, width)
