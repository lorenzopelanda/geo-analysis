import rasterio
import numpy as np
import json
import osmnx as ox
from DistanceInterface import DistanceInterface
ox.settings.use_cache = False

class DistanceCoprnicus(DistanceInterface):

    def __init__(self, raster_data, vector_traffic_area, ghs_pop_data):
        self.copernicus_green = raster_data
        self.vector_traffic_area = vector_traffic_area
        self.preprocessed_graph = None
        self.ghs_pop_data = ghs_pop_data
        self._green_positions_cache = {}


    def get_nearest_green_position(self, lat, lon):

        if not (isinstance(lat, (int, float)) and isinstance(lon, (int, float))):
            raise ValueError("Coordinates not valid")

        data = self.copernicus_green['data']
        transform = self.copernicus_green['transform']

        col, row = [int(round(i)) for i in ~transform * (lon, lat)]

        if not (0 <= row < data.shape[0] and 0 <= col < data.shape[1]):
            raise IndexError("Starting point outside raster bounds")

        search_radius = 3
        for dr in range(-search_radius, search_radius + 1):
            for dc in range(-search_radius, search_radius + 1):
                if (0 <= (row + dr) < data.shape[0] and
                        0 <= (col + dc) < data.shape[1]):
                    if data[row + dr, col + dc] == 1:
                        nearest_lon, nearest_lat = rasterio.transform.xy(
                            transform,
                            row + dr,
                            col + dc
                        )
                        return (nearest_lat, nearest_lon)

        green_indices = np.argwhere(data == 1)
        if len(green_indices) == 0:
            raise ValueError("No green areas found in the raster")

        # Conversion to geographic coordinates
        green_coords = np.array([
            rasterio.transform.xy(transform, idx[0], idx[1])
            for idx in green_indices
        ])

        # Distance calculation with haversine
        lons = green_coords[:, 0]
        lats = green_coords[:, 1]
        distances = self._haversine_vectorized(lon, lat, lons, lats)

        # Find the nearest green area
        nearest_idx = np.argmin(distances)
        nearest_lon, nearest_lat = green_coords[nearest_idx]

        return (nearest_lat, nearest_lon)

    def _haversine_vectorized(self, lon1, lat1, lons2, lats2):

        R = 6371  # Earth radius in km


        lat1 = np.radians(lat1)
        lon1 = np.radians(lon1)
        lats2 = np.radians(lats2)
        lons2 = np.radians(lons2)

        dlat = lats2 - lat1
        dlon = lons2 - lon1

        # Vectorized formula
        a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lats2) * np.sin(dlon / 2) ** 2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

        return R * c


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
        total_time_minutes = self._calculate_travel_time(total_distance_meters, transport_mode)

        return json.dumps({"distance_km": round(total_distance,4), "estimated_time_minutes": total_time_minutes, "lat": nearest_lat, "lon": nearest_lon})
 
