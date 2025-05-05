import json
import osmnx as ox
import numpy as np
import logging
from tqdm import tqdm
from typing import Tuple
from greento.utils.geo import geo
from .interface import interface
class copernicus(interface):
    """
    A class to calculate metrics using Copernicus data.

    Attributes
    ----------
    copernicus_green : dict
        The Copernicus green area data containing 'data', 'transform', 'crs', and 'shape'.
    vector_traffic_area : tuple
        A tuple containing two GeoDataFrames: nodes and edges for traffic area.
    ghs_pop_data : dict
        The GHS-POP data containing 'data', 'transform', 'crs', and 'shape'.

    Methods
    -------
    green_area_per_person() -> str
        Calculates the green area per person in the given raster and population data.
    get_isochrone_green(lat: float, lon: float, max_time: float, network_type: str) -> str
        Calculates the reachable green areas within a given time from a starting point.
    _estimate_distance_from_time(time_seconds: float, transport_mode: str) -> float
        Estimates the distance that can be traveled in a given time for a specific transport mode.
    """

    def __init__(self, raster_data: dict, vector_traffic_area: Tuple, ghs_pop_data: dict) -> None: 
        """
        Initializes the MetricsCopernicus class with Copernicus green area data, traffic area, and population data.

        Parameters
        ----------
        raster_data : dict
            The Copernicus green area data containing 'data', 'transform', 'crs', and 'shape'.
        vector_traffic_area : tuple
            A tuple containing two GeoDataFrames: nodes and edges for traffic area.
        ghs_pop_data : dict
            The GHS-POP data containing 'data', 'transform', 'crs', and 'shape'.

        Returns
        -------
        None
        """
        self.copernicus_green = raster_data
        self.vector_traffic_area = vector_traffic_area
        self.ghs_pop_data = ghs_pop_data
        
    def green_area_per_person(self) -> str:
        """
        Calculates the green area per person in the given raster and population data.

        Returns
        -------
        str
            A JSON string containing the green area per person.
        """
        with tqdm(total=100, desc="Calculating Copernicus green area per person", leave=False) as pbar:
            ghspop_data = self.ghs_pop_data['data']
            copernicus_data = self.copernicus_green['data']
            pbar.update(20)

            num_green_pixels = np.count_nonzero(copernicus_data)
            pbar.update(20)
            total_green_area = num_green_pixels * 100  # sqm

            total_population = np.sum(ghspop_data)
            pbar.update(40)
            if total_population == 0:
                pbar.update(20)
                pbar.set_description("Finished calculating Copernicus green area per person")
                pbar.close()
                return json.dumps({'green_area_per_person': float('inf')})
            else:
                green_area_per_person = round(total_green_area / total_population, 4)
                pbar.update(20)
                pbar.set_description("Finished calculating Copernicus green area per person")
                pbar.close()
                return json.dumps({'green_area_per_person': green_area_per_person})


    def get_isochrone_green(self, lat: float, lon: float, max_time: float, network_type: str) -> str:
        """
        Calculates the reachable green areas within a given time from a starting point.

        Parameters
        ----------
        lat : float
            The latitude of the starting point.
        lon : float
            The longitude of the starting point.
        max_time : float
            The maximum travel time in minutes.
        network_type : str
            The type of transport network (e.g., 'walk', 'bike', 'drive', 'all_public', 'drive_public').

        Returns
        -------
        str
            A JSON string containing the reachable green areas in the selected max time with the selected transport mode.

        Raises
        ------
        ValueError
            If the input parameters are invalid or the traffic area is not reachable.
        """
        with tqdm(total=100, desc="Calculating Copernicus isochrone green area", unit="%", leave=False) as pbar:
            logger = logging.getLogger(__name__)
            if not (isinstance(lat, (int, float)) and isinstance(lon, (int, float))):
                logger.error("Coordinates not valid")
                return None
            pbar.update(5)
            if not isinstance(max_time, (int, float)) or max_time <= 0:
                logger.error("Max time not valid")
                return None

            valid_transport_modes = ['walk', 'bike', 'drive', 'all_public', 'drive_public']
            if network_type not in valid_transport_modes:
                logger.error(f"Transport mode not valid. Choose from: {', '.join(valid_transport_modes)}")
                return None
            pbar.update(5)
            if not hasattr(self, 'vector_traffic_area') or self.vector_traffic_area is None:
                logger.error("Traffic area not reachable")
                return None

            speed_kmh = {
                'walk': 5,
                'bike': 15,
                'drive': 30,
                'all_public': 30,
                'drive_public': 30
            }.get(network_type, 5)

            nodes, edges = self.vector_traffic_area
            G = ox.graph_from_gdfs(nodes, edges)  
            start_node, _ = ox.distance.nearest_nodes(G, X=lon, Y=lat, return_dist=True)
            pbar.update(10)
            FIXED_DELAYS = {
                'walk': 0,
                'bike': 30,  # take/return bike
                'drive': 180,  # parking + take the car
                'all_public': 420,  # walk to the stop (3 min) + estimated wait (4 min)
                'drive_public': 180  # wait + call
            }

            fixed_delay = FIXED_DELAYS.get(network_type, 0)

            travel_time_seconds = (max_time * 60) - fixed_delay

            if travel_time_seconds <= 0:
                logger = logging.getLogger(__name__)
                logger.warning(f"Time after delays ({fixed_delay / 60} min) is not enough to travel.")
                return None

            for u, v, data in G.edges(data=True):
                if 'travel_time' not in data and 'length' in data:
                    length_m = data['length']
                    data['travel_time'] = length_m / (speed_kmh * 1000 / 3600)
            pbar.update(10)
            reachable_nodes = {}
            visited = set()
            queue = [(start_node, 0)]  

            while queue:
                current_node, current_time = queue.pop(0)

                if current_node in visited:
                    continue

                visited.add(current_node)
                pbar.update(5)
                if pbar.n > 75:
                    pbar.n = 75
                if current_node in G.nodes:
                    node_data = G.nodes[current_node]
                    reachable_nodes[current_node] = {
                        'y': node_data.get('y'),
                        'x': node_data.get('x'),
                        'time': current_time
                    }

                for neighbor in G.neighbors(current_node):
                    if neighbor not in visited:
                        edges = G.get_edge_data(current_node, neighbor).values()
                        edge_time = min(edge.get('travel_time', float('inf')) for edge in edges)

                        new_time = current_time + edge_time

                        if new_time <= travel_time_seconds:
                            queue.append((neighbor, new_time))
            pbar.update(10)
            if not reachable_nodes:
                logger = logging.getLogger(__name__)
                logger.warning("No reachable nodes within the time limit.")
                return None

            reachable_coords = [(data['y'], data['x']) for node_id, data in reachable_nodes.items()]

            data = self.copernicus_green['data']
            transform = self.copernicus_green['transform']

            total_pixels = 0
            green_area_pixels = 0
            green_accessibility = {}

            for lat_point, lon_point in reachable_coords:
                try:
                    row, col = [int(i) for i in ~transform * (lon_point, lat_point)]

                    if 0 <= row < data.shape[0] and 0 <= col < data.shape[1]:
                        total_pixels += 1
                        pixel_value = data[row, col]

                        if pixel_value == 1:
                            green_area_pixels += 1

                            node_data = next(
                                (d for n, d in reachable_nodes.items() if d['y'] == lat_point and d['x'] == lon_point),
                                None)
                            if node_data:
                                time_to_node = node_data['time']
                                distance_meters = self._estimate_distance_from_time(time_to_node, network_type)
                                travel_time = geo()._calculate_travel_time(distance_meters, network_type)
                                green_accessibility[node_data['x']] = {
                                    'time_minutes': travel_time,
                                    'distance_meters': round(distance_meters, 2),
                                    'lat': lat_point,
                                    'lon': lon_point
                                }
                except Exception:
                    continue
            pbar.update(10)
            green_percentage = (green_area_pixels / max(1, total_pixels)) * 100 if total_pixels > 0 else 0

            pixel_area_sqm = 100  # 10m x 10m
            green_area_sqm = green_area_pixels * pixel_area_sqm

            result = {
                "max_time": max_time,
                "transport_mode": network_type,
                "green_area_percentage": round(green_percentage, 2),
                "green_area_sqm": round(green_area_sqm, 2),
                "green_accessibility": list(green_accessibility.values()),
            }
            pbar.update(5)
            if pbar.n > 100:
                pbar.n = 100
                pbar.last_print_n = 100
            pbar.set_description("Finished calculating Copernicus isochrone green area")
            pbar.close()

            return json.dumps(result)

    def _estimate_distance_from_time(self, time_seconds: float, transport_mode: str) -> float:
        """
        Estimates the distance that can be traveled in a given time for a specific transport mode.

        Parameters
        ----------
        time_seconds : float
            The time available for travel in seconds.
        transport_mode : str
            The type of transport network ('walk', 'bike', 'drive', 'all_public', 'drive_public').

        Returns
        -------
        float
            The estimated distance that can be traveled in meters.
        """
        # Speed constants in m/s
        SPEEDS = {
            'walk': 5 / 3.6,
            'bike': 15 / 3.6,
            'drive': 30 / 3.6,
            'all_public': 30 / 3.6,
            'drive_public': 30 / 3.6
        }

        DELAY_FACTORS = {
            'walk': 1.15,
            'bike': 1.2,
            'drive': 1.25,
            'all_public': 1.10,
            'drive_public': 1.25
        }

        speed = SPEEDS.get(transport_mode, SPEEDS['walk'])
        delay_factor = DELAY_FACTORS.get(transport_mode, 1.0)

        distance = time_seconds * speed / delay_factor

        return distance