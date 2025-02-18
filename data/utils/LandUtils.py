from rasterio.warp import reproject, Resampling, calculate_default_transform
import numpy as np
import rasterio
from rasterio.features import rasterize


class LandUtils:
    def adjust_detail_level(self, target_area, source_area):
        """
        Get population data for a given area using Target and Source data,
        ensuring both outputs have matching resolution and extent.
        """
        target_data= target_area['data']
        target_transform = target_area['transform']
        target_crs = target_area['crs']
        target_shape = target_area['shape']

        source_data = source_area['data']
        source_transform = source_area['transform']
        source_crs = source_area['crs']
        source_shape = source_area['shape']

        # Handle different shapes of Target data
        if len(target_shape) == 2:
            target_height, target_width = target_shape
        elif len(target_shape) == 3:
            _, target_height, target_width = target_shape
        else:
            raise ValueError(f"Unexpected shape for: {target_shape}")

        target_transform = target_transform

        # Create an empty array for the resampled Source data
        source_resampled = np.empty((target_height, target_width), dtype=source_data.dtype)

        # Reproject the Source data to match the Target resolution and extent
        reproject(
            source=source_data,
            destination=source_resampled,
            src_transform=source_transform,
            src_crs=source_crs,
            dst_transform=target_transform,
            dst_crs=target_crs,
            resampling=Resampling.bilinear
        )

        # Handle Target data dimensions
        if target_data.ndim == 4:
            target_data = target_data[0, 0, :, :]
        elif target_data.ndim == 3:
            target_data = target_data[0, :, :]

        return {
            "target": {
                "data": target_data,
                "transform": target_transform,
                "crs": target_crs,
                "shape": target_shape
            },
            "source": {
                "data": source_resampled,
                "transform": target_transform,
                "crs": target_crs,
                "shape": (target_height, target_width)
            }
        }

    def vector_to_raster(self, vector_layer, reference_raster):
        """
        Convert a vector area into a raster with the same resolution and extent as a reference raster.

        Parameters:
            vector_layer (GeoDataFrame): A GeoDataFrame containing tag geometries from OpenStreetMap.
            reference_raster (tuple): A tuple containing the reference raster's data, transform, CRS, and shape.

        Returns:
            dict: A dictionary containing the rasterized data and metadata.
        """

        ref_data = reference_raster['data']
        ref_transform = reference_raster['transform']
        ref_crs = reference_raster['crs']
        ref_shape = reference_raster['shape']

        # Ensure the vector data is in the same CRS as the reference raster
        if vector_layer.crs != ref_crs:
            vector_layer = vector_layer.to_crs(ref_crs)

        # Rasterize the vector geometries
        shapes = [(geom, 1) for geom in vector_layer.geometry if geom is not None]

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

    def transform_raster_to_crs(self, src_data, src_transform, src_crs, shape, dst_crs):
        """
        Transform a raster to a new CRS with a different resolution and extent.
        """
        # Check shape dimensions
        if len(shape) == 2:
            height, width = shape
            count = 1
        elif len(shape) == 3:
            count, height, width = shape
        else:
            raise ValueError("Shape of the data incorrect!")

        bounds = rasterio.transform.array_bounds(height, width, src_transform)

        # Calculate the new transform and shape
        transform, width, height = calculate_default_transform(
            src_crs,
            dst_crs,
            width,
            height,
            *bounds
        )

        # Empty array to store the transformed data
        dst_data = np.empty((count, int(height), int(width)), dtype=src_data.dtype)

        for i in range(count):
            reproject(
                source=src_data[i] if count > 1 else src_data,
                destination=dst_data[i] if count > 1 else dst_data[0],
                src_transform=src_transform,
                src_crs=src_crs,
                dst_transform=transform,
                dst_crs=dst_crs,
                resampling=Resampling.nearest
            )

        return {
            'data': dst_data,
            'crs': dst_crs,
            'transform': transform
        }



