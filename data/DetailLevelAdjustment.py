import rasterio
from rasterio.warp import reproject, Resampling
import numpy as np

class DetailLevelAdjustment:

    def adjust_detail_level(self, copernicus_area, ghspop_area):
        """
        Get population data for a given area using Copernicus and GHS-POP data,
        ensuring both outputs have matching resolution, extent, and coordinates.
        """
        copernicus_data, copernicus_transform, copernicus_crs, copernicus_shape = copernicus_area
        ghs_data, ghs_transform, ghs_crs, ghs_shape = ghspop_area

        if ghs_crs != 'EPSG:4326':
            ghs_resampled_4326 = np.empty_like(ghs_data)
            reproject(
                source=ghs_data,
                destination=ghs_resampled_4326,
                src_transform=ghs_transform,
                src_crs=ghs_crs,
                dst_transform=ghs_transform,
                dst_crs='EPSG:4326',
                resampling=Resampling.nearest
            )
            ghs_data = ghs_resampled_4326
            ghs_crs = 'EPSG:4326'

        target_height, target_width = copernicus_shape
        target_transform = copernicus_transform

        ghs_resampled = np.empty((target_height, target_width), dtype=ghs_data.dtype)

        reproject(
            source=ghs_data,
            destination=ghs_resampled,
            src_transform=ghs_transform,
            src_crs=ghs_crs,
            dst_transform=target_transform,
            dst_crs=copernicus_crs,
            resampling=Resampling.bilinear
        )

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

        if copernicus_data.ndim == 4:
            copernicus_data = copernicus_data[0, 0, :, :]
        elif copernicus_data.ndim == 3:
            copernicus_data = copernicus_data[0, :, :]

        # Salva i dati Copernicus
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
