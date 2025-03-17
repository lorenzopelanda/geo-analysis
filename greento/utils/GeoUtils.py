import requests
import rasterio
import numpy as np
from rasterio.warp import reproject, Resampling


class GeoUtils:
    def _calculate_travel_time(self, distance_meters, transport_mode):
        """
        Calculate the estimated travel time for a given distance and transport mode.
        """
        # Speed constants in km/h
        SPEEDS = {
            'walk': 1.4,  # 5 km/h
            'bike': 4.17,  # 15 km/h
            'drive': 8.33,  # 30 km/h (urban)
            'all_public': 8.33,  # 30 km/h
            'drive_service': 8.33  # as drive
        }

        # Medium time of fixed delays in minutes
        FIXED_DELAYS = {
            'walk': 0,
            'bike': 30,  # take/return bike
            'drive': 180,  # parking + take the car
            'all_public': 420,  # walk to the stop (3 min) + estimated wait (4 min)
            'drive_service': 180  # wait + call
        }

        # Delay factors depending on traffic and semaphores
        DELAY_FACTORS = {
            'walk': 1.15,  # semaphores for pedestrians
            'bike': 1.2,  # semaphores and traffic
            'drive': 1.25,  # traffic and semaphores
            'all_public': 1.10,  # traffic and semaphores
            'drive_service': 1.25  # as drive
        }

        # Base speed and time calculation
        base_speed = SPEEDS[transport_mode]
        base_time_seconds = distance_meters / base_speed

        # Apply delay factors and fixed delays
        total_time_seconds = (base_time_seconds * DELAY_FACTORS[transport_mode]) + FIXED_DELAYS[transport_mode]

        # Convert total time to minutes
        total_time_minutes = round(total_time_seconds / 60, 1)

        return total_time_minutes
    
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