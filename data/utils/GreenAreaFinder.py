from shapely.geometry import Point, mapping, box, MultiPolygon
import rasterio
import numpy as np
import json
import pandas as pd
import geopandas as gpd
from rtree import index
from typing import Tuple
import osmnx as ox
from geopy.distance import geodesic
from scipy.spatial import cKDTree
ox.settings.use_cache = False

class GreenAreaFinder:
    def __init__(self, raster_data, vector_traffic_area):
        self.copernicus_raster = raster_data
        self.vector_traffic_area = vector_traffic_area
        self.preprocessed_graph = None

    def calculate_travel_time(self, distance_meters, transport_mode):
        """
        Calculate the estimated travel time for a given distance and transport mode.
        """
        # Speed constants in km/h
        SPEEDS = {
            'walk': 1.4,  # 5 km/h
            'bike': 4.17,  # 15 km/h
            'car': 8.33,  # 30 km/h (urban)
            'bus': 5.56,  # 20 km/h
            'tram': 6.94,  # 25 km/h
            'metro': 13.89,  # 50 km/h
            'taxi': 8.33  # as car
        }

        # Medium time of fixed delays in minutes
        FIXED_DELAYS = {
            'walk': 0,
            'bike': 30,  # take/return bike
            'car': 180,  # parking + take the car
            'bus': 420,  # walk to the stop (3 min) + estimated wait (4 min)
            'tram': 420,  # walk to the stop (3 min) + estimated wait (4 min)
            'metro': 300,  # walk to the stop (3 min) + estimated wait (2 min)
            'taxi': 180  # wait + call
        }

        # Delay factors depending on traffic and semaphores
        DELAY_FACTORS = {
            'walk': 1.15,  # semaphores for pedestrians
            'bike': 1.2,  # semaphores and traffic
            'car': 1.25,  # traffic and semaphores
            'bus': 1.2,  # bus stopes and traffic
            'tram': 1.15,  # tram stops and traffic
            'metro': 1.0,  # no delay
            'taxi': 1.25  # as car
        }

        # Base speed and time calculation
        base_speed = SPEEDS[transport_mode]
        base_time_seconds = distance_meters / base_speed

        # Apply delay factors and fixed delays
        total_time_seconds = (base_time_seconds * DELAY_FACTORS[transport_mode]) + FIXED_DELAYS[transport_mode]

        # Convert total time to minutes
        total_time_minutes = round(total_time_seconds / 60, 1)

        return total_time_minutes

    def get_nearest_green_position(self, lat, lon):
        """
        Find the nearest green area to the given coordinates.
        It uses the Copernicus raster, it is optimised for large datasets.
        """
        if not (isinstance(lat, (int, float)) and isinstance(lon, (int, float))):
            raise ValueError("Coordinates must be valid")

        # Costants for green areas in the Copernicus raster
        GREEN_AREAS = frozenset([10, 20, 30, 60, 95, 100])

        data = self.copernicus_raster['data']
        transform = self.copernicus_raster['transform']

        # Convert coordinates to raster indices
        row, col = [int(i) for i in ~transform * (lon, lat)]

        # Check if the point is outside the raster bounds
        if not (0 <= row < data.shape[0] and 0 <= col < data.shape[1]):
            raise IndexError("Point outside raster bounds")

        # Check if point is already in a green area
        if data[row, col] in GREEN_AREAS:
            return lat, lon

        # Create a mask for green areas
        green_mask = np.isin(data, list(GREEN_AREAS))
        green_indices = np.argwhere(green_mask)

        # Optimize the ouput for large datasets
        if len(green_indices) > 10000:
            step = len(green_indices) // 10000
            green_indices = green_indices[::step]

        # Converts green indices to geographic coordinates
        green_coords = np.array([
            rasterio.transform.xy(transform, idx[0], idx[1])
            for idx in green_indices
        ])

        # Find the nearest green area
        tree = cKDTree(green_coords)
        _, idx = tree.query((lon, lat))
        longitude, latitude = green_coords[idx]

        return (latitude, longitude)

    def direction_to_green(self, lat, lon, transport_mode):
        """
        Calculate the distance and estimated time to reach the nearest green area
        starting from a given position, using the vector_traffic_area graph.
        """

        # Reset preprocessed_graph if None
        if hasattr(self, "preprocessed_graph") and self.preprocessed_graph is None:
            delattr(self, "preprocessed_graph")

        nearest_lat, nearest_lon = self.get_nearest_green_position(lat, lon)

        if not hasattr(self, "preprocessed_graph"):
            G = self.vector_traffic_area
            if isinstance(G, tuple) and len(G) == 2:
                gdf_nodes, gdf_edges = G
                # Check nodes coordinates
                if 'x' not in gdf_nodes.columns or 'y' not in gdf_nodes.columns:
                    gdf_nodes['x'] = gdf_nodes.geometry.x
                    gdf_nodes['y'] = gdf_nodes.geometry.y

                G = ox.graph_from_gdfs(gdf_nodes, gdf_edges)
                if G is None:
                    raise ValueError("Failed to create graph from GeoDataFrames")

                # Check if graph has nodes
                if len(G.nodes()) == 0:
                    raise ValueError("Graph has no nodes")
            else:
                raise ValueError(f"Unexpected vector_traffic_area type: {type(G)}")

            G = ox.routing.add_edge_speeds(G)
            G = ox.routing.add_edge_travel_times(G)

            self.preprocessed_graph = G

        # Use preprocessed graph
        G = self.preprocessed_graph

        # Checks if nodes have x and y coordinates
        for node_id, data in G.nodes(data=True):
            if "x" not in data or "y" not in data:
                raise ValueError("Node must have coordinates 'x' e 'y'")

        # Finds the nearest nodes in the graph
        orig_node = ox.distance.nearest_nodes(G, X=lon, Y=lat)
        dest_node = ox.distance.nearest_nodes(G, X=nearest_lon, Y=nearest_lat)

        # Calculate the shortest path (Djikstra algorithm and travel_time as weight)

        route = ox.shortest_path(G, orig_node, dest_node, weight="travel_time")

        # Calculate the total distance of the path
        total_distance = sum(G[u][v][0].get("length", 0) for u, v in zip(route[:-1], route[1:])) / 1000
        total_distance_meters = total_distance*1000
        # Calculate the total time of the path
        total_time_minutes = self.calculate_travel_time(total_distance_meters, transport_mode)

        return json.dumps({"distance_km": round(total_distance,4), "estimated_time_minutes": total_time_minutes})

