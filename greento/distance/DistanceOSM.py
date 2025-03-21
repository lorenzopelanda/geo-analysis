import json
import osmnx as ox
import numpy as np
import rasterio
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
import networkx as nx
from tqdm import tqdm
from scipy.spatial import cKDTree
from scipy.ndimage import label, center_of_mass
from math import radians, sin, cos, sqrt, atan2
from greento.utils.GeoUtils import GeoUtils
from .DistanceInterface import DistanceInterface
ox.settings.use_cache = False

class DistanceOSM(DistanceInterface):
    def __init__(self, osm_green, vector_traffic_area):
        self.osm_green = osm_green
        self.vector_traffic_area = vector_traffic_area
        self.preprocessed_graph = None
        self._green_positions_cache = {}

    def get_nearest_green_position(self, lat, lon,):
        """
        Finds the nearest green area from a given starting point using a raster dataset and a traffic network graph.

        Args:
            lat (float): Latitude of the starting point.
            lon (float): Longitude of the starting point.

        Returns:
            tuple: A tuple containing the latitude and longitude of the nearest green area, or None if no green areas are found.

        Raises:
            ValueError: If there is an error calculating the nearest green point.
        """
        with tqdm(total=100, desc="Processing nearest green position", leave=False) as pbar:
            nodes, edges = self.vector_traffic_area
            raster_data = self.osm_green['data']
            transform = self.osm_green['transform']

            G = ox.graph_from_gdfs(nodes, edges)
            
            nearest_node = ox.distance.nearest_nodes(G, X=lon, Y=lat)
            
            pbar.update(10)
            structure = np.ones((3, 3), dtype=int)
            labeled, num_features = label(raster_data == 1, structure=structure)
            
            if num_features == 0:
                print("No green areas found in the raster")
                return None

            centroids_pixels = center_of_mass(raster_data == 1, labeled, index=range(1, num_features+1))
            pbar.update(10)
            green_coords = []
            for row, col in centroids_pixels:
                lon_pixel, lat_pixel = transform * (col + 0.5, row + 0.5)
                green_coords.append((lat_pixel, lon_pixel))

            distances_euclidian = np.array([GeoUtils().haversine_distance(lat, lon, gp_lat, gp_lon) for gp_lat, gp_lon in green_coords])
            pbar.update(10)
            if len(green_coords) < 2000:
                max_green_points = len(green_coords)
            elif len(green_coords) < 10000:
                max_green_points = len(green_coords) // 5
            else:
                max_green_points = 5000

            indices_sorted = np.argsort(distances_euclidian)[:max_green_points]
            green_coords_filtered = [green_coords[i] for i in indices_sorted]

            node_points = np.array([(data['y'], data['x']) for _, data in G.nodes(data=True)])
            node_ids = list(G.nodes())
            tree = cKDTree(node_points)
            pbar.update(20)
            green_nodes = []
            batch_size = 100
            for i in range(0, len(green_coords_filtered), batch_size):
                batch = green_coords_filtered[i:i+batch_size]
                batch_points = np.array(batch)
                distances_batch, indices_batch = tree.query(batch_points, k=1)
                for j, (dist, idx) in enumerate(zip(distances_batch, indices_batch)):
                    green_lat, green_lon = batch[j]
                    closest_node = node_ids[idx]
                    green_nodes.append((green_lat, green_lon, closest_node, dist * 111000))
            pbar.update(20)
            try:
                distances = nx.single_source_dijkstra_path_length(G, nearest_node, weight='length', cutoff=100000)
            except nx.NetworkXError as e:
                raise ValueError("Error calculating nearest green point") from e
            pbar.update(20)
            min_distance = float('inf')
            closest_green_point = None
            for green_lat, green_lon, node, node_dist in green_nodes:
                if node in distances:
                    total_distance = distances[node] + node_dist
                    if total_distance < min_distance:
                        min_distance = total_distance
                        closest_green_point = (green_lat, green_lon)
            pbar.update(10)
            pbar.set_description("Nearest green position found")
            pbar.close()
            return closest_green_point

    def directions(self, lat1, lon1, lat2, lon2, transport_mode):
        """
        Calculate the shortest path and estimated travel time between two points using a traffic network graph.

        Args:
            lat1 (float): Latitude of the starting point.
            lon1 (float): Longitude of the starting point.
            lat2 (float): Latitude of the destination point.
            lon2 (float): Longitude of the destination point.
            transport_mode (str): Mode of transport (e.g., "walk", "bike", "drive").

        Returns:
            str: A JSON string containing the total distance in kilometers and the estimated travel time in minutes.

        Raises:
            ValueError: If there is an error creating the graph or if the graph has no nodes.
        """
        with tqdm (total=100, desc="Calculating the direction", leave=False) as pbar:
            if hasattr(self, "preprocessed_graph") and self.preprocessed_graph is None:
                delattr(self, "preprocessed_graph")

            if not hasattr(self, "preprocessed_graph"):
                G = self.vector_traffic_area
                if isinstance(G, tuple) and len(G) == 2:
                    gdf_nodes, gdf_edges = G
                    if 'x' not in gdf_nodes.columns or 'y' not in gdf_nodes.columns:
                        gdf_nodes['x'] = gdf_nodes.geometry.x
                        gdf_nodes['y'] = gdf_nodes.geometry.y

                    G = ox.graph_from_gdfs(gdf_nodes, gdf_edges)
                    pbar.update(20)
                    if G is None:
                        raise ValueError("Failed to create graph from GeoDataFrames")

                    if len(G.nodes()) == 0:
                        raise ValueError("Graph has no nodes")
                else:
                    raise ValueError(f"Unexpected vector_traffic_area type: {type(G)}")

                G = ox.routing.add_edge_speeds(G)
                G = ox.routing.add_edge_travel_times(G)
                pbar.update(20)
                self.preprocessed_graph = G

            if pbar.n<40:
                pbar.update(40)
            G = self.preprocessed_graph
            pbar.update(30)
            for node_id, data in G.nodes(data=True):
                if "x" not in data or "y" not in data:
                    raise ValueError("Node must have coordinates 'x' e 'y'")

            orig_node = ox.distance.nearest_nodes(G, X=lon1, Y=lat1)
            dest_node = ox.distance.nearest_nodes(G, X=lon2, Y=lat2)
            pbar.update(20)

            route = ox.shortest_path(G, orig_node, dest_node, weight="travel_time")
            total_distance = sum(G[u][v][0].get("length", 0) for u, v in zip(route[:-1], route[1:])) / 1000
            total_distance_meters = total_distance * 1000
            total_time_minutes = GeoUtils()._calculate_travel_time(total_distance_meters, transport_mode)
            pbar.update(10)
            pbar.set_description("Direction calculated")
            pbar.close()

            return json.dumps({"distance_km": round(total_distance, 4), "estimated_time_minutes": total_time_minutes})

    