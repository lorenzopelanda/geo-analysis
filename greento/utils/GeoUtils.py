import requests
import rasterio
import numpy as np
from tqdm import tqdm
from rasterio.warp import reproject, Resampling

class GeoUtils:
    """
    A class to provide utility functions for geographical data.

    Methods:
    -------
    _calculate_travel_time(distance_meters, transport_mode):
        Calculates the estimated travel time for a given distance and transport mode.
    get_coordinates_from_address(address):
        Gets the latitude and longitude coordinates for a given address.
    get_address_from_coordinates(lat, lon):
        Gets the address for given latitude and longitude coordinates.
    get_coordinates_max_population(ghs_pop):
        Gets the coordinates of the cell with the maximum population.
    adjust_detail_level(osm, copernicus, ghs_pop):
        Adjusts the detail level of the given raster datasets to match the highest resolution.
    """
    def _calculate_travel_time(self, distance_meters, transport_mode):
        """
        Calculates the estimated travel time for a given distance and transport mode.

        Parameters:
        ----------
        distance_meters : float
            The distance to travel in meters.
        transport_mode : str
            The mode of transport (e.g., 'walk', 'bike', 'drive', 'all_public', 'drive_service').

        Returns:
        -------
        float
            The estimated travel time in minutes.
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

        base_speed = SPEEDS[transport_mode]
        base_time_seconds = distance_meters / base_speed

        total_time_seconds = (base_time_seconds * DELAY_FACTORS[transport_mode]) + FIXED_DELAYS[transport_mode]

        total_time_minutes = round(total_time_seconds / 60, 1)

        return total_time_minutes
    
    def get_coordinates_from_address(self, address):
        """
        Gets the latitude and longitude coordinates for a given address.

        Parameters:
        ----------
        address : str
            The address to geocode.

        Returns:
        -------
        tuple
            A tuple containing the latitude and longitude coordinates.

        Raises:
        ------
        ValueError
            If the address is not found.
        """
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": address,
            "format": "json",
            "limit": 1
        }
        headers = {
            "User-Agent": "GreenTo/1.0"
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
        Gets the address for given latitude and longitude coordinates.

        Parameters:
        ----------
        lat : float
            The latitude coordinate.
        lon : float
            The longitude coordinate.

        Returns:
        -------
        str
            The address corresponding to the given coordinates.

        Raises:
        ------
        ValueError
            If the address is not found.
        """
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json"
        }
        headers = {
            "User-Agent": "GreenTo/1.0"
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
        Gets the coordinates of the cell with the maximum population.

        Parameters:
        ----------
        ghs_pop : dict
            The GHS-POP data containing 'data' and 'transform'.

        Returns:
        -------
        tuple
            A tuple containing the latitude and longitude coordinates of the cell with the maximum population.
        """
        with tqdm(total=100, desc="Getting coordinates of maximum population") as pbar:
            data = ghs_pop['data']
            transform = ghs_pop['transform']
            pbar.update(30)
            idx = np.unravel_index(np.argmax(data, axis=None), data.shape)
            pbar.update(50)
            lon, lat = rasterio.transform.xy(transform, idx[0], idx[1])
            pbar.update(20)
            pbar.set_description("Coordinates of maximum population found")

        return (lat, lon)
    
    def adjust_detail_level(self, osm, copernicus, ghs_pop):
        """
        Adjusts the detail level of the given raster datasets to match the highest resolution.

        Parameters:
        ----------
        osm : dict
            The OSM data containing 'data', 'transform', 'crs', and 'shape'.
        copernicus : dict
            The Copernicus data containing 'data', 'transform', 'crs', and 'shape'.
        ghs_pop : dict
            The GHS-POP data containing 'data', 'transform', 'crs', and 'shape'.

        Returns:
        -------
        dict
            A dictionary containing the adjusted raster datasets with the highest resolution.
        
        Raises:
        ------
        ValueError
            If one or more raster datasets are None or if the shape of the target data is unexpected.
        """
        if osm is None or copernicus is None or ghs_pop is None:
            raise ValueError("One or more raster datasets are None. Check rasterization process.")

        area_1_pixel_size = abs(copernicus['transform'][0] * copernicus['transform'][4])
        area_2_pixel_size = abs(osm['transform'][0] * osm['transform'][4])
        area_3_pixel_size = abs(ghs_pop['transform'][0] * ghs_pop['transform'][4])

        pixel_sizes = [(area_1_pixel_size, copernicus, 'copernicus'),
                       (area_2_pixel_size, osm, 'osm'),
                       (area_3_pixel_size, ghs_pop, 'ghs_pop')]
        pixel_sizes.sort(key=lambda x: x[0])  

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
            'highest_res_area': pixel_sizes[0][2]  
        }

        with tqdm(total=len(pixel_sizes), desc="Adjusting detail level") as pbar:
            for pixel_size, area, area_name in pixel_sizes:
                source_data = area['data']
                source_transform = area['transform']
                source_crs = area['crs']

                if area_name == pixel_sizes[0][2]:
                    result[area_name] = {
                        "data": source_data,
                        "transform": target_transform,
                        "crs": target_crs,
                        "shape": (target_height, target_width)
                    }
                else:
                    source_resampled = np.empty((target_height, target_width), dtype=source_data.dtype)

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
                pbar.update(1)    

        return result