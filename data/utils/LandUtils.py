from rasterio.warp import reproject, Resampling
import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import rasterize

class LandUtils:

    def adjust_detail_level(self, copernicus_area, ghspop_area):
        """
        Get population data for a given area using Copernicus and GHS-POP data,
        ensuring both outputs have matching resolution and extent.
        """
        copernicus_data, copernicus_transform, copernicus_crs, copernicus_shape = copernicus_area
        ghs_data, ghs_transform, ghs_crs, ghs_shape = ghspop_area

        # Resample GHS-POP data to match the resolution of Copernicus data
        target_height, target_width = copernicus_shape
        target_transform = copernicus_transform

        # Create an empty array for the resampled GHS-POP data
        ghs_resampled = np.empty((target_height, target_width), dtype=ghs_data.dtype)

        # Reproject the GHS-POP data to match the Copernicus resolution and extent
        reproject(
            source=ghs_data,
            destination=ghs_resampled,
            src_transform=ghs_transform,
            src_crs=ghs_crs,
            dst_transform=target_transform,
            dst_crs=copernicus_crs,
            resampling=Resampling.bilinear
        )

        # Save resampled GHS-POP data
        with rasterio.open(
                "ghspop_resampled.tif",
                'w',
                driver='GTiff',
                height=target_height,
                width=target_width,
                count=1,
                dtype=ghs_resampled.dtype,
                crs=copernicus_crs,
                transform=target_transform,
        ) as dst:
            dst.write(ghs_resampled, 1)

        # Handle Copernicus data dimensions
        if copernicus_data.ndim == 4:
            copernicus_data = copernicus_data[0, 0, :, :]
        elif copernicus_data.ndim == 3:
            copernicus_data = copernicus_data[0, :, :]

        # Save Copernicus data
        with rasterio.open(
                "copernicus_area.tif",
                'w',
                driver='GTiff',
                height=copernicus_shape[0],
                width=copernicus_shape[1],
                count=1,
                dtype=copernicus_data.dtype,
                crs=copernicus_crs,
                transform=copernicus_transform,
        ) as dst:
            dst.write(copernicus_data, 1)

        return {
            "copernicus": {
                "data": copernicus_data,
                "transform": copernicus_transform,
                "crs": copernicus_crs,
                "shape": copernicus_shape
            },
            "ghspop": {
                "data": ghs_resampled,
                "transform": target_transform,
                "crs": copernicus_crs,
                "shape": (target_height, target_width)
            }
        }



    def vector_to_raster(self, osm_layer, reference_raster):
        """
        Convert a vector area (OSM buildings) into a raster with the same resolution and extent as a reference raster.

        Parameters:
            osm_layer (GeoDataFrame): A GeoDataFrame containing building geometries from OpenStreetMap.
            reference_raster (tuple): A tuple containing the reference raster's data, transform, CRS, and shape.

        Returns:
            dict: A dictionary containing the rasterized building data and metadata.
        """

        ref_data, ref_transform, ref_crs, ref_shape = reference_raster

        # Ensure the vector data is in the same CRS as the reference raster
        if osm_layer.crs != ref_crs:
            osm_layer = osm_layer.to_crs(ref_crs)

        # Rasterize the building geometries
        shapes = [(geom, 1) for geom in osm_layer.geometry if geom is not None]

        # Create an empty raster with the same shape as the reference raster
        rasterized = np.zeros(ref_shape, dtype=np.uint8)

        # Rasterize the vector data
        rasterized= rasterize(
            shapes=shapes,
            out_shape=ref_shape,
            transform=ref_transform,
            fill=0,
            dtype=np.uint8,
            all_touched=True
        )

        return {
            "data": rasterized,
            "transform": ref_transform,
            "crs": ref_crs,
            "shape": ref_shape
        }