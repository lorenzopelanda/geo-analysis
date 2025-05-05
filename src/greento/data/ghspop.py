import shutil
import geopandas as gpd
from shutil import rmtree
from shapely.geometry import Point
import requests
import zipfile
import os
import osmnx as ox
import numpy as np
import logging
import rasterio
import rasterio.mask
from typing import Dict, List, Tuple, Union
from affine import Affine
from rasterio.io import MemoryFile
from rasterio.merge import merge
from shapely.geometry import box
from greento.boundingbox import boundingbox
from greento.data.ghspop_io import ghspop_io
from greento.data.interface import interface
from tqdm import tqdm

ox.settings.use_cache = True

class ghspop(interface):
    """
    A class to handle downloading, processing, and cropping of GHS-POP data.

    Parameters
    ----------
    shapefile : str
        The path to the shapefile containing tile information.
    extracted_dir : str, optional
        The directory to store extracted files (default is "extracted_files").

    Methods
    -------
    __remove_existing_directory()
        Removes the existing directory used for temporary storage.
    __load_shapefile()
        Loads the shapefile containing tile information.
    __get_tiles_for_bounds(bounds, tiles_gdf)
        Gets the tile IDs that intersect with the given bounding box.
    __merge_tiles(tiles)
        Merges multiple raster tiles into a single raster.
    __process_single_tile(tile_id)
        Downloads and processes a single tile by extracting its raster data.
    __download_and_process_tiles(tile_ids)
        Downloads and processes multiple tiles.
    __crop_bounds(data, transform, bounds)
        Crops the raster data to the specified bounding box.
    get_data(bounding_box)
        Downloads and processes GHS-POP data for the specified bounding box.
    """

    def __init__(self,shapefile: str, extracted_dir: str="extracted_files") -> None:
        """
        Initializes the GHS-POP class with the shapefile and extracted directory.

        Parameters
        ----------
        shapefile : str
            The path to the shapefile containing tile information.
        extracted_dir : str, optional
            The directory to store extracted files (default is "extracted_files").

        Returns
        -------
        None
        """
        self.extracted_dir = extracted_dir
        self.shapefile_path = shapefile

    def __remove_existing_directory(self) -> None:
        """
        Removes the existing directory used for temporary storage.

        Returns
        -------
        None
        """
        if os.path.exists(self.extracted_dir):
            rmtree(self.extracted_dir)

    def __load_shapefile(self) -> gpd.GeoDataFrame:
        """
        Loads the shapefile containing tile information.

        Returns
        -------
        geopandas.GeoDataFrame
            A GeoDataFrame containing the tile information.
        """
        tiles_gdf = gpd.read_file(self.shapefile_path)
        if tiles_gdf.crs != "EPSG:4326":
            tiles_gdf = tiles_gdf.to_crs("EPSG:4326")
        return tiles_gdf

    # def __get_tile_id(self, tiles_gdf: gpd.GeoDataFrame, point_gdf: gpd.GeoDataFrame) -> str:
    #     """
    #     Gets the tile ID for a given point.

    #     Args:
    #         tiles_gdf (geopandas.GeoDataFrame): GeoDataFrame containing tile information.
    #         point_gdf (geopandas.GeoDataFrame): GeoDataFrame containing the point geometry.

    #     Returns:
    #         str or None: The tile ID if found, otherwise None.
    #     """
    #     current_tile = tiles_gdf[tiles_gdf.contains(point_gdf.geometry.iloc[0])]
    #     if not current_tile.empty:
    #         return current_tile.iloc[0]['tile_id']
    #     return None

    def __get_tiles_for_bounds(self, bounds: "boundingbox", tiles_gdf: gpd.GeoDataFrame) -> List[str]:
        """
        Gets the tile IDs that intersect with the given bounding box.

        Parameters
        ----------
        bounds : boundingbox
            The bounding box for which to find intersecting tiles.
        tiles_gdf : geopandas.GeoDataFrame
            A GeoDataFrame containing tile information.

        Returns
        -------
        list of str
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

    

    def __merge_tiles(self, tiles: List[Tuple[np.ndarray, Affine, str, Tuple[int, int]]]) -> Tuple[np.ndarray, Affine, str, Tuple[int, int]]:
        """
        Merges multiple raster tiles into a single raster.

        Parameters
        ----------
        tiles : list of tuple
            A list of tuples containing raster data, transform, CRS, and shape.

        Returns
        -------
        tuple
            A tuple containing the merged raster data, transform, CRS, and shape.
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
    def __process_single_tile(self, tile_id: str) -> Tuple[np.ndarray, Affine, str, Tuple[int, int]]:
        """
        Downloads and processes a single tile by extracting its raster data.

        Parameters
        ----------
        tile_id : str
            The ID of the tile to download and process.

        Returns
        -------
        tuple
            A tuple containing:
            - data (numpy.ndarray): The raster data of the tile.
            - transform (affine.Affine): The affine transform of the raster data.
            - crs (str): The coordinate reference system of the raster data.
            - shape (tuple of int): The shape of the raster data (height, width).

        Raises
        ------
        Exception
            If an error occurs during the download or processing of the tile.
        """
        logger = logging.getLogger(__name__)
        try:
            zip_path = ghspop_io.__download_tile(tile_id)
            if not zip_path:
                logger.warning(f"Failed to download tile {tile_id}")
                return None

            tif_path = ghspop_io.__extract_tif_file(zip_path)
            if tif_path is None:
                logger.warning(f"Failed to extract TIF file from {zip_path}")
                return None

            with rasterio.open(tif_path) as dataset:
                data = dataset.read(1)
                return data, dataset.transform, dataset.crs, dataset.shape

        except Exception as e:
            logger.error(f"Error processing tile {tile_id}: {str(e)}")
            return None

    def __download_and_process_tiles(self, tile_ids: List[str]) -> Tuple[np.ndarray, Affine, str, Tuple[int, int]]:
        """
        Downloads and processes multiple tiles by merging their raster data.

        Parameters
        ----------
        tile_ids : list of str
            A list of tile IDs to download and process.

        Returns
        -------
        tuple
            A tuple containing:
            - data (numpy.ndarray): The merged raster data of the tiles.
            - transform (affine.Affine): The affine transform of the merged raster data.
            - crs (str): The coordinate reference system of the merged raster data.
            - shape (tuple of int): The shape of the merged raster data (height, width).

        Raises
        ------
        ValueError
            If no tile IDs are provided for download.

        Notes
        -----
        Temporary files created during the process are cleaned up after processing.
        """
        if not tile_ids:
            raise ValueError("No tile IDs provided for download.")

        downloaded_tiles = []
        processed_paths = []
        logger = logging.getLogger(__name__)
        try:
            for tile_id in tile_ids:
                tile_data = self.__process_single_tile(tile_id)
                if tile_data:
                    downloaded_tiles.append(tile_data)
                    processed_paths.append(os.path.join(self.extracted_dir,f"GHS_POP_{tile_id}.tif"))

            if not downloaded_tiles:
                logger.error("No valid tiles downloaded.")

            if len(downloaded_tiles) == 1:
                result = downloaded_tiles[0]
            else:
                result = self.__merge_tiles(downloaded_tiles)

            return result

        finally:
            ghspop_io.__cleanup_files(processed_paths)

    def __crop_bounds(self, data: np.ndarray, transform: Affine, bounds: "boundingbox") -> Tuple[np.ndarray, Affine, str, Tuple[int, int]]:
        """
        Crops the raster data to the specified bounding box.

        Parameters
        ----------
        data : numpy.ndarray
            The raster data to crop.
        transform : affine.Affine
            The affine transform of the raster data.
        bounds : boundingbox
            The bounding box to crop the raster data.

        Returns
        -------
        tuple
            A tuple containing the cropped raster data, transform, CRS, and shape.
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

    def get_data(self, bounding_box: "boundingbox") -> Dict[str, Union[np.ndarray, Affine, str, Tuple[int, int]]]:
        """
        Downloads and processes GHS-POP data for the specified bounding box.

        Parameters
        ----------
        bounding_box : boundingbox
            The bounding box for which to download and process GHS-POP data.

        Returns
        -------
        dict
            A dictionary containing the processed GHS-POP data, transform, CRS, and shape.

            Keys:
            - 'data': numpy.ndarray
                The raster data.
            - 'transform': affine.Affine
                The affine transform of the raster data.
            - 'crs': str
                The coordinate reference system of the raster data.
            - 'shape': tuple of int
                The shape of the raster data.
        """
        logger = logging.getLogger(__name__)
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
                logger.error("No tiles found for the given bounding box.")
            
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