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
from greento.data.DataInterface import DownloaderInterface
from tqdm import tqdm

ox.settings.use_cache = True

class GHSPOPDownloader(DownloaderInterface):
    """
    A class to download and process GHS-POP data.

    Attributes:
    ----------
    shapefile_path : str
        Path to the shapefile containing tile information.
    extracted_dir : str
        Directory to store extracted files.

    Methods:
    -------
    __remove_existing_directory():
        Removes the existing directory if it exists.
    __load_shapefile():
        Loads the shapefile and converts it to the correct CRS.
    __get_tile_id(tiles_gdf, point_gdf):
        Gets the tile ID for a given point.
    __download_tile(tile_id):
        Downloads a tile based on the tile ID.
    __extract_tif_file(zip_path):
        Extracts the TIF file from the downloaded zip archive.
    __get_tiles_for_bounds(bounds, tiles_gdf):
        Gets the tile IDs for the given bounding box.
    __cleanup_files(file_paths):
        Cleans up processed files and directories.
    __merge_tiles(tiles):
        Merges multiple GHS-POP tiles into a single raster.
    __process_single_tile(tile_id):
        Processes a single GHS-POP tile.
    __download_and_process_tiles(tile_ids):
        Downloads and processes GHS-POP tiles based on the provided tile IDs.
    __crop_bounds(data, transform, bounds):
        Crops the given data to the specified bounding box.
    get_data(bounding_box):
        Downloads and processes GHS-POP data for the given bounding box.
    """
    def __init__(self,shapefile, extracted_dir="extracted_files" ):
        """
        Initializes the GHSPOPDownloader with the shapefile path and extracted directory.

        Parameters:
        ----------
        shapefile : str
            Path to the shapefile containing tile information.
        extracted_dir : str, optional
            Directory to store extracted files (default is "extracted_files").
        """
        self.extracted_dir = extracted_dir
        self.shapefile_path = shapefile

    def __remove_existing_directory(self):
        """
        Removes the existing directory if it exists.
        """
        if os.path.exists(self.extracted_dir):
            rmtree(self.extracted_dir)

    def __load_shapefile(self):
        """
        Loads the shapefile and converts it to the correct CRS.

        Returns:
        -------
        geopandas.GeoDataFrame
            The loaded shapefile as a GeoDataFrame.
        """
        tiles_gdf = gpd.read_file(self.shapefile_path)
        if tiles_gdf.crs != "EPSG:4326":
            tiles_gdf = tiles_gdf.to_crs("EPSG:4326")
        return tiles_gdf

    def __get_tile_id(self, tiles_gdf, point_gdf):
        """
        Gets the tile ID for a given point.

        Parameters:
        ----------
        tiles_gdf : geopandas.GeoDataFrame
            GeoDataFrame containing tile information.
        point_gdf : geopandas.GeoDataFrame
            GeoDataFrame containing the point geometry.

        Returns:
        -------
        str or None
            The tile ID if found, otherwise None.
        """
        current_tile = tiles_gdf[tiles_gdf.contains(point_gdf.geometry.iloc[0])]
        if not current_tile.empty:
            return current_tile.iloc[0]['tile_id']
        return None

    def __download_tile(self, tile_id):
        """
        Downloads a tile based on the tile ID.

        Parameters:
        ----------
        tile_id : str
            The tile ID to download.

        Returns:
        -------
        str or None
            The path to the downloaded zip file if successful, otherwise None.
        """
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
        Extracts the TIF file from the downloaded zip archive.

        Parameters:
        ----------
        zip_path : str
            The path to the zip file.

        Returns:
        -------
        str or None
            The path to the extracted TIF file if successful, otherwise None.
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

            if os.path.exists(zip_path):
                os.remove(zip_path)

            return tif_path

        except Exception as e:
            print(f"Error during TIF extraction: {str(e)}")
            return None

    def __get_tiles_for_bounds(self, bounds, tiles_gdf):
        """
        Gets the tile IDs for the given bounding box.

        Parameters:
        ----------
        bounds : BoundingBox
            The bounding box for which to get tile IDs.
        tiles_gdf : geopandas.GeoDataFrame
            GeoDataFrame containing tile information.

        Returns:
        -------
        list
            A list of tile IDs that intersect with the bounding box.
        """
        bbox = box(bounds.min_x, bounds.min_y, bounds.max_x, bounds.max_y)

        bbox_gdf = gpd.GeoDataFrame([{'geometry': bbox}], crs="EPSG:4326")

        intersecting_tiles = tiles_gdf[tiles_gdf.intersects(bbox_gdf.geometry[0])]

        tile_ids = []
        for _, row in intersecting_tiles.iterrows():
            tile_id = row['tile_id']
            if tile_id:
                tile_ids.append(tile_id)

        return tile_ids

    def __cleanup_files(self, file_paths):
        """
        Cleans up processed files and directories.

        Parameters:
        ----------
        file_paths : list
            List of file paths to clean up.
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
        Merges multiple GHS-POP tiles into a single raster.

        Parameters:
        ----------
        tiles : list
            List of tuples containing tile data, transform, CRS, and shape.

        Returns:
        -------
        tuple
            Merged data, transform, CRS, and shape.
        """
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

        merged_data, merged_transform = merge(temp_datasets)

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
        Processes a single GHS-POP tile.

        Parameters:
        ----------
        tile_id : str
            The tile ID to process.

        Returns:
        -------
        tuple or None
            The tile data, transform, CRS, and shape if successful, otherwise None.
        """
        try:
            zip_path = self.__download_tile(tile_id)
            if not zip_path:
                print(f"Failed to download tile {tile_id}")
                return None

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
        Downloads and processes GHS-POP tiles based on the provided tile IDs.

        Parameters:
        ----------
        tile_ids : list
            List of tile IDs to download and process.

        Returns:
        -------
        tuple
            Merged data, transform, CRS, and shape.

        Raises:
        ------
        ValueError
            If no tile IDs are provided or no valid tiles are downloaded.
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

            if len(downloaded_tiles) == 1:
                result = downloaded_tiles[0]
            else:
                result = self.__merge_tiles(downloaded_tiles)

            return result

        finally:
            self.__cleanup_files(processed_paths)

    def __crop_bounds(self, data, transform, bounds):
        """
        Crops the given data to the specified bounding box.

        Parameters:
        ----------
        data : numpy.ndarray
            The data to crop.
        transform : affine.Affine
            The transform of the data.
        bounds : BoundingBox
            The bounding box to crop to.

        Returns:
        -------
        tuple
            Cropped data, transform, CRS, and shape.
        """
        crs = "EPSG:4326"
        bbox = box(bounds.min_x, bounds.min_y, bounds.max_x, bounds.max_y)
        geo = gpd.GeoDataFrame({'geometry': [bbox]}, crs=crs)
        geo = geo.to_crs(crs=rasterio.crs.CRS.from_string(crs))

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

                out_image, out_transform = rasterio.mask.mask(
                    dataset, geo.geometry, crop=True
                )

        return out_image, out_transform, crs, out_image.shape

    def get_data(self, bounding_box):
        """
        Downloads and processes GHS-POP data for the given bounding box.

        Parameters:
        ----------
        bounding_box : BoundingBox
            The bounding box for which to download data.

        Returns:
        -------
        dict
            A dictionary containing the downloaded data, transform, CRS, and shape.
        """
        steps=["Removing existing directory","Loading shapefile","Getting tiles for bounds","Downloading and processing tiles","Cropping bounds"]
        with tqdm(total=100, desc="Overall Progress", unit = "steps", leave=False) as pbar:
            self.__remove_existing_directory()
            pbar.update(10)
            
            pbar.set_description(steps[1])
            tiles_gdf = self.__load_shapefile()
            pbar.update(10)

            pbar.set_description(steps[2])
            tiles_to_download = self.__get_tiles_for_bounds(bounding_box, tiles_gdf)
            pbar.update(10)

            if not tiles_to_download:
                raise ValueError("No tiles to download for the given bounds.")
            
            pbar.set_description(steps[3])
            ghs_data, ghs_transform, ghs_crs, ghs_shape = self.__download_and_process_tiles(tiles_to_download)
            pbar.update(50)
            pbar.set_description(steps[4])
            ghs_data_cropped, ghs_transform_cropped, ghs_crs_cropped, ghs_shape_cropped = self.__crop_bounds(ghs_data, ghs_transform, bounding_box)
            pbar.update(10)
            ghs_data_cropped = np.squeeze(ghs_data_cropped, axis=0)
            self.__remove_existing_directory()
            pbar.update(10)
            pbar.set_description("GHS-POP data downloaded")
            pbar.close()
            return {"data":ghs_data_cropped, "transform":ghs_transform_cropped, "crs": ghs_crs_cropped,"shape": ghs_shape_cropped}