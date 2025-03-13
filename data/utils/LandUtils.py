from rasterio.warp import reproject, Resampling, calculate_default_transform
import numpy as np
import rasterio
import requests
from rasterio.features import rasterize


class LandUtils:

    def adjust_detail_level(self, osm, copernicus, ghs_pop):
        """

        """
        # Calculate pixel size/resolution for all areas
        # Smaller pixel size = higher resolution
        if osm is None or copernicus is None or ghs_pop is None:
            raise ValueError("One or more raster datasets are None. Check rasterization process.")

        area_1_pixel_size = abs(copernicus['transform'][0] * copernicus['transform'][4])
        area_2_pixel_size = abs(osm['transform'][0] * osm['transform'][4])
        area_3_pixel_size = abs(ghs_pop['transform'][0] * ghs_pop['transform'][4])

        # Determine which area has the highest resolution (smallest pixel size)
        pixel_sizes = [(area_1_pixel_size, copernicus, 'copernicus'),
                       (area_2_pixel_size, osm, 'osm'),
                       (area_3_pixel_size, ghs_pop, 'ghs_pop')]
        pixel_sizes.sort(key=lambda x: x[0])  # Sort by pixel size (ascending)

        # The first element has the highest resolution (smallest pixel size)
        target_area = pixel_sizes[0][1]

        target_transform = target_area['transform']
        target_crs = target_area['crs']
        target_shape = target_area['shape']

        if len(target_shape) == 2:
            target_height, target_width = target_shape
        elif len(target_shape) == 3:
            _, target_height, target_width = target_shape
        else:
            raise ValueError(f"Unexpected shape for target: {target_shape}")

        result = {
            'copernicus': None,
            'osm': None,
            'ghs_pop': None,
            'highest_res_area': pixel_sizes[0][2]  # Store which area had highest resolution
        }

        # Process all areas (including the high-res one for consistency)
        for pixel_size, area, area_name in pixel_sizes:
            source_data = area['data']
            source_transform = area['transform']
            source_crs = area['crs']

            # If this is already the highest resolution area, just use the original data
            if area_name == pixel_sizes[0][2]:
                result[area_name] = {
                    "data": source_data,
                    "transform": target_transform,
                    "crs": target_crs,
                    "shape": (target_height, target_width)
                }
            else:
                source_resampled = np.empty((target_height, target_width), dtype=source_data.dtype)

                # Reproject the source data to match the target resolution and extent
                reproject(
                    source=source_data,
                    destination=source_resampled,
                    src_transform=source_transform,
                    src_crs=source_crs,
                    dst_transform=target_transform,
                    dst_crs=target_crs,
                    resampling=Resampling.bilinear
                )

                result[area_name] = {
                    "data": source_resampled,
                    "transform": target_transform,
                    "crs": target_crs,
                    "shape": (target_height, target_width)
                }

        return result

    def vector_to_raster(self, vector_data, reference_raster):
        """
        Rasterize the OpenStreetMap vector data using a reference raster.

        Args:
            vector_data (tuple): A tuple containing nodes (GeoDataFrame of point data) and edges (GeoDataFrame of line/polygon data).
            reference_raster (dict): Reference raster containing 'data', 'transform', 'crs', and 'shape'.

        Returns:
            dict: Rasterized output with 'data', 'transform', 'crs', and 'shape'.
        """
        nodes, edges = vector_data
        ref_crs = reference_raster['crs']

        # Rasterize nodes (points)
        node_shapes = [(geom, 1) for geom in nodes.geometry if geom is not None]
        node_rasterized = rasterize(
            shapes=node_shapes,
            out_shape=reference_raster['shape'],
            transform=reference_raster['transform'],
            fill=0,
            dtype=np.uint8,
            all_touched=True
        )

        # Rasterize edges (lines or polygons)
        edge_shapes = [(geom, 1) for geom in edges.geometry if geom is not None]
        edge_rasterized = rasterize(
            shapes=edge_shapes,
            out_shape=reference_raster['shape'],
            transform=reference_raster['transform'],
            fill=0,
            dtype=np.uint8,
            all_touched=True
        )

        # Combine node and edge rasters
        combined_raster = np.maximum(node_rasterized, edge_rasterized)  # Combine both rasters by taking the maximum

        return {
            "data": combined_raster,
            "transform": reference_raster['transform'],
            "crs": ref_crs,
            "shape": reference_raster['shape']
        }

    def raster_to_crs(self, raster,dst_crs):
        """
        Transform a raster to a new CRS with a different resolution and extent.
        """
        src_data = raster['data']
        src_transform = raster['transform']
        src_crs = raster['crs']
        shape = raster['shape']
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

    def get_coordinates_from_address(self, address):
        """
        Get the latitude and longitude coordinates for a given address.
        """

        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": address,
            "format": "json",
            "limit": 1
        }
        headers = {
            "User-Agent": "GeoAnalysis/1.0 (geodatalibrary@gmail.com)"
        }
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return lat, lon
        else:
            raise ValueError("Address not found")

    def get_address_from_coordinates(self, lat, lon):
        """
        Get the address for given latitude and longitude coordinates.
        """
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json"
        }
        headers = {
            "User-Agent": "GeoAnalysis/1.0 (geodatalibrary@gmail.com)"
        }

        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        if "display_name" in data:
            return data["display_name"]
        else:
            raise ValueError("Address not found for the given coordinates")

    def get_coordinates_max_population(self, ghs_pop):
        """
        Get the coordinates of the cell with the maximum population.
        """
        data = ghs_pop['data']
        transform = ghs_pop['transform']

        idx = np.unravel_index(np.argmax(data, axis=None), data.shape)

        lon, lat = rasterio.transform.xy(transform, idx[0], idx[1])

        return (lat, lon)



