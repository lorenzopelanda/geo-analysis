from typing import Tuple, List, Optional

import rasterio
import tempfile
import os
from rasterio.enums import Resampling
from rasterio.transform import from_bounds
from rasterio.merge import merge
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling
import geopandas as gpd
from shapely.geometry import Point, box
import numpy as np
import shutil
from data.CopernicusDownloader import CopernicusDownloader
from data.GHSPOPDownloader import GHSPOPDownloader

shapefile_path = "../tiling_schema/WGS84_tile_schema.shp"



class GHSPOPCopernicusMerged:
    def download_and_process_tiles(self, tile_ids: List[str], ghs_pop) -> Tuple[
        np.ndarray, rasterio.Affine, str, Tuple[int, int]]:
        """
        Download and process GHS-POP tiles based on provided tile IDs.
        """
        if not tile_ids:
            raise ValueError("No tile IDs provided for download.")

        downloaded_tiles = []
        processed_paths = []  # Keep track of processed files

        try:
            for tile_id in tile_ids:
                # Download and process each tile
                tile_data = self._process_single_tile(tile_id, ghs_pop)
                if tile_data:
                    downloaded_tiles.append(tile_data)
                    processed_paths.append(os.path.join(ghs_pop.extracted_dir,
                                                        f"GHS_POP_E2030_GLOBE_R2023A_4326_30ss_V1_0_{tile_id}.tif"))

            if not downloaded_tiles:
                raise ValueError("Failed to download any valid tiles.")

            # Handle single vs multiple tiles
            if len(downloaded_tiles) == 1:
                result = downloaded_tiles[0]
            else:
                result = self._merge_tiles(downloaded_tiles)

            return result

        finally:
            # Clean up extracted files after processing is complete
            self.cleanup_files(processed_paths, ghs_pop)

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
                data = dataset.read(1)  # Read first band
                return data, dataset.transform, dataset.crs, dataset.shape

        except Exception as e:
            print(f"Error processing tile {tile_id}: {str(e)}")
            return None

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
            merged_data[0],  # First band of merged data
            merged_transform,
            tiles[0][2],  # Use CRS from first tile
            merged_data.shape[1:]  # Shape excluding bands dimension
        )

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

        # Clean up extracted directory if it's empty
        try:
            if os.path.exists(ghs_pop.extracted_dir) and not os.listdir(ghs_pop.extracted_dir):
                shutil.rmtree(ghs_pop.extracted_dir)
        except Exception as e:
            print(f"Error removing directory {ghs_pop.extracted_dir}: {str(e)}")

    def get_copernicus_population_area(self, bbox, address, use_oidc, copernicus_downloader, **kwargs):
        """
        Get population data for a given area using Copernicus and GHS-POP data.
        """
        # Download Copernicus raster data
        raster_data, copernicus_transform, copernicus_crs, copernicus_shape = (
            copernicus_downloader.download_raster_area(bbox, use_oidc, **kwargs)
        )

        if raster_data.ndim == 4:
            # If we have a 4D array (bands, time, height, width), take the first band and time
            raster_data = raster_data[0, 0, :, :]
        elif raster_data.ndim == 3:
            # If we have a 3D array (bands, height, width), take the first band
            raster_data = raster_data[0, :, :]

        with tempfile.NamedTemporaryFile(delete=False, suffix='.tif') as tmpfile:
            temp_raster_path = tmpfile.name
            with rasterio.open(
                    temp_raster_path,
                    'w',
                    driver='GTiff',
                    height=raster_data.shape[0],
                    width=raster_data.shape[1],
                    count=1,
                    dtype=raster_data.dtype,
                    crs=copernicus_crs,
                    transform=copernicus_transform,
            ) as dst:
                dst.write(raster_data, 1)

        # Initialize GHS-POP downloader
        ghs_pop = GHSPOPDownloader(address, shapefile_path)

        # Get Copernicus bounds
        copernicus_bounds = rasterio.transform.array_bounds(
            copernicus_shape[0],
            copernicus_shape[1],
            copernicus_transform
        )

        # Get required GHS-POP tiles
        tiles_gdf = self.load_shapefile()
        tiles_to_download = self.get_tiles_for_bounds(copernicus_bounds, tiles_gdf, ghs_pop)

        if not tiles_to_download:
            raise ValueError("No tiles to download for the given bounds.")

        ghs_data, ghs_transform, ghs_crs, ghs_shape = self.download_and_process_tiles(tiles_to_download, ghs_pop)

        # Save GHS-POP data to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.tif') as tmpfile:
            temp_ghs_path = tmpfile.name
            with rasterio.open(
                    temp_ghs_path,
                    'w',
                    driver='GTiff',
                    height=ghs_data.shape[0],
                    width=ghs_data.shape[1],
                    count=1,
                    dtype=ghs_data.dtype,
                    crs=ghs_crs,
                    transform=ghs_transform,
            ) as dst:
                dst.write(ghs_data, 1)

        ghs_bounds = rasterio.transform.array_bounds(ghs_shape[0], ghs_shape[1], ghs_transform)
        new_transform = from_bounds(*ghs_bounds, ghs_shape[1], ghs_shape[0])

        copernicus_bbox = box(*copernicus_bounds)
        ghs_bbox = box(*ghs_bounds)
        if not ghs_bbox.contains(copernicus_bbox):
            raise ValueError("The bounding boxes of Copernicus and GHS-POP data do not intersect.")

        copernicus_resampled = self.resample_copernicus_to_ghspop(
            raster_data, copernicus_transform, copernicus_crs, ghs_shape, ghs_transform, ghs_crs
        )

        copernicus_geometry = [copernicus_bbox]
        ghs_clipped, _ = mask(
            dataset=rasterio.open(temp_ghs_path),
            shapes=copernicus_geometry,
            crop=True
        )



        copernicus_tif_path = "copernicus_resampled.tif"

        with rasterio.open(
                copernicus_tif_path,
                'w',
                driver='GTiff',
                height=copernicus_resampled.shape[0],
                width=copernicus_resampled.shape[1],
                count=1,
                dtype=copernicus_resampled.dtype,
                crs=copernicus_crs,
                transform=new_transform,
        ) as dst:
            dst.write(copernicus_resampled, 1)

        # Save GHSPOP clipped data to a .tif file
        ghs_tif_path = "ghspop_clipped.tif"
        with rasterio.open(
                ghs_tif_path,
                'w',
                driver='GTiff',
                height=ghs_clipped.shape[1],
                width=ghs_clipped.shape[2],
                count=1,
                dtype=ghs_clipped.dtype,
                crs=ghs_crs,
                transform=ghs_transform,
        ) as dst:
            dst.write(ghs_clipped[0], 1)

        return {
            "copernicus": {
                "data": copernicus_resampled,
                "transform": new_transform,
                "crs": copernicus_crs,
                "shape": ghs_shape
            },
            "ghspop": {
                "data": ghs_clipped[0],
                "transform": ghs_transform,
                "crs": ghs_crs
            }
        }



    def resample_copernicus_to_ghspop(self, copernicus_data, copernicus_transform, copernicus_crs, ghs_shape, ghs_transform, ghs_crs):
        """
        Resample Copernicus data to match the resolution of GHS-POP data.
        """

        copernicus_resolution = (copernicus_transform[0], -copernicus_transform[4])
        ghs_resolution = (ghs_transform[0], -ghs_transform[4])
        print(f"Copernicus resolution: {copernicus_resolution}, GHS-POP resolution: {ghs_resolution}")

        ghs_bounds = rasterio.transform.array_bounds(ghs_shape[0], ghs_shape[1], ghs_transform)
        new_transform = from_bounds(*ghs_bounds, ghs_shape[1], ghs_shape[0])

        copernicus_resampled = np.empty((ghs_shape[0], ghs_shape[1]), dtype=np.float32)

        # Risampling dei dati Copernicus alla risoluzione di GHS-POP
        reproject(
            source=copernicus_data,
            destination=copernicus_resampled,
            src_transform=copernicus_transform,
            src_crs=copernicus_crs,
            dst_transform=new_transform,
            dst_crs=ghs_crs,
            resampling=Resampling.average,
        )

        resampled_resolution = (new_transform[0], -new_transform[4])
        print(f"Resampled Copernicus resolution: {resampled_resolution}")
        return copernicus_resampled

    def load_shapefile(self):
        tiles_gdf = gpd.read_file(shapefile_path)
        if tiles_gdf.crs != "EPSG:4326":
            tiles_gdf = tiles_gdf.to_crs("EPSG:4326")
        print(f"Tiles CRS: {tiles_gdf.crs}")
        return tiles_gdf
    def create_point_gdf(self):
        point = Point(self.lat, self.lon)
        return gpd.GeoDataFrame([{'geometry': point}], crs="EPSG:4326")

    def get_tiles_for_bounds(self, bounds, tiles_gdf, ghs_pop):
        # Create a bounding box from the bounds
        bbox = box(bounds[0], bounds[1], bounds[2], bounds[3])
        bbox_gdf = gpd.GeoDataFrame([{'geometry': bbox}], crs="EPSG:4326")

        # Find intersecting tiles
        intersecting_tiles = tiles_gdf[tiles_gdf.intersects(bbox_gdf.geometry[0])]

        # Get tile IDs for intersecting tiles
        tile_ids = []
        for _, row in intersecting_tiles.iterrows():
            tile_id = row['tile_id']  # Assuming 'tile_id' is the column name for tile IDs
            if tile_id:
                tile_ids.append(tile_id)

        return tile_ids

    def merge_ghspop_tiles(self, tiles):
        # List to store the opened datasets
        datasets = []

        for tile in tiles:
            # Open each tile and append to the datasets list
            datasets.append(rasterio.open(tile))

        # Merge the datasets
        mosaic, out_transform = merge(datasets)

        # Get the CRS and shape from the first dataset (assuming all tiles have the same CRS and shape)
        out_crs = datasets[0].crs
        out_shape = mosaic.shape[1:]

        # Close all datasets
        for dataset in datasets:
            dataset.close()
        return mosaic, out_transform, out_crs, out_shape

