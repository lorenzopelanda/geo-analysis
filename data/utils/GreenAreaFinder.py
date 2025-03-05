import rasterio
import numpy as np
import json
import osmnx as ox
from scipy.spatial import cKDTree
ox.settings.use_cache = True

class GreenAreaFinder:
    def __init__(self, raster_data, vector_traffic_area, ghs_pop_data):
        self.copernicus_raster = raster_data
        self.vector_traffic_area = vector_traffic_area
        self.preprocessed_graph = None
        self.ghs_pop_data = ghs_pop_data
        self._green_positions_cache = {}

    def green_area_per_person(self, green_areas=None):
        """
        Calculate the green area per person in the given raster and population data.
        """
        if green_areas is None:
            green_areas = frozenset([10, 20, 30, 60, 95, 100])

        ghspop_data = self.ghs_pop_data['data']
        copernicus_data = self.copernicus_raster['data']

        green_mask = np.isin(copernicus_data, list(green_areas))

        total_green_area = np.sum(green_mask) * 100 # squaremeters

        total_population = np.sum(ghspop_data)

        if total_population == 0:
            return float('inf')
        else:
            return round(total_green_area / total_population, 4)

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

    def get_nearest_green_position(self, lat, lon, green_areas=None):
        """
        Find the nearest green area to the given coordinates.
        It uses the Copernicus raster, it is optimised for large datasets.
        """
        if not (isinstance(lat, (int, float)) and isinstance(lon, (int, float))):
            raise ValueError("Coordinates must be valid")

        # Costants for green areas in the Copernicus raster
        if green_areas is None:
            green_areas = frozenset([10, 20, 30, 60, 95, 100])

        data = self.copernicus_raster['data']
        transform = self.copernicus_raster['transform']

        # Convert coordinates to raster indices
        row, col = [int(i) for i in ~transform * (lon, lat)]

        # Check if the point is outside the raster bounds
        if not (0 <= row < data.shape[0] and 0 <= col < data.shape[1]):
            raise IndexError("Point outside raster bounds")

        # Check if point is already in a green area
        if data[row, col] in green_areas:
            return lat, lon

        # Create a mask for green areas
        green_mask = np.isin(data, list(green_areas))
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

    def direction_to_green(self, lat, lon, transport_mode, green_areas=None):
        """
        Calculate the distance and estimated time to reach the nearest green area
        starting from a given position, using the vector_traffic_area graph.
        """

        # Reset preprocessed_graph if None
        if hasattr(self, "preprocessed_graph") and self.preprocessed_graph is None:
            delattr(self, "preprocessed_graph")

        nearest_lat, nearest_lon = self.get_nearest_green_position(lat, lon,green_areas)
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


    def get_isochrone_green(self, lat, lon, max_time, network_type):
        """
       Calculate the reachable green areas within a given time from a starting point.
        """
        if not (isinstance(lat, (int, float)) and isinstance(lon, (int, float))):
            raise ValueError("Coordinates not valid")

        if not isinstance(max_time, (int, float)) or max_time <= 0:
            raise ValueError("Max time not valid")

        valid_transport_modes = ['walk', 'bike', 'car', 'bus', 'tram', 'metro', 'taxi']
        if network_type not in valid_transport_modes:
            raise ValueError(f"Transport mode not valid. Choose from: {', '.join(valid_transport_modes)}")

        # Copernicus green constants
        GREEN_AREAS = frozenset([10, 20, 30, 60, 95, 100])

        if not hasattr(self, 'vector_traffic_area') or self.vector_traffic_area is None:
            raise ValueError("Traffic area not reachable")

        speed_kmh = {
            'walk': 5,
            'bike': 15,
            'car': 30,
            'bus': 20,
            'tram': 25,
            'metro': 50,
            'taxi': 30
        }.get(network_type, 5)

        nodes, edges = self.vector_traffic_area
        G = ox.graph_from_gdfs(nodes, edges)  # Ristructure of the graph
        # Find nearest node from strating point
        start_node, _ = ox.distance.nearest_nodes(G, X=lon, Y=lat, return_dist=True)

        FIXED_DELAYS = {
            'walk': 0,
            'bike': 30,  # take/return bike
            'car': 180,  # parking + take the car
            'bus': 420,  # walk to the stop (3 min) + estimated wait (4 min)
            'tram': 420,  # walk to the stop (3 min) + estimated wait (4 min)
            'metro': 300,  # walk to the stop (3 min) + estimated wait (2 min)
            'taxi': 180  # wait + call
        }

        fixed_delay = FIXED_DELAYS.get(network_type, 0)

        # Time available for travel in seconds
        travel_time_seconds = (max_time * 60) - fixed_delay


        if travel_time_seconds <= 0:
            return json.dumps({
                "error": f"Time after delays is ({fixed_delay / 60} min) not enough to travel"
            })

        for u, v, data in G.edges(data=True):
            if 'travel_time' not in data and 'length' in data:
                lunghezza_m = data['length']
                data['travel_time'] = lunghezza_m / (speed_kmh * 1000 / 3600)

        # Visit the graph to find reachable nodes
        reachable_nodes = {}
        visited = set()
        queue = [(start_node, 0)]  # (node, time)

        while queue:
            current_node, current_time = queue.pop(0)

            if current_node in visited:
                continue

            visited.add(current_node)

            # Put the current node in the reachable nodes
            if current_node in G.nodes:
                node_data = G.nodes[current_node]
                reachable_nodes[current_node] = {
                    'y': node_data.get('y'),
                    'x': node_data.get('x'),
                    'time': current_time
                }

            # Visit the neighbors
            for neighbor in G.neighbors(current_node):
                if neighbor not in visited:
                    edges = G.get_edge_data(current_node, neighbor).values()
                    edge_time = min(edge.get('travel_time', float('inf')) for edge in edges)

                    new_time = current_time + edge_time

                    # Add the neighbor to the queue if the time is within the limit
                    if new_time <= travel_time_seconds:
                        queue.append((neighbor, new_time))

        if not reachable_nodes:
            return json.dumps({"error": "No reachable green area for the time limit"})

        # Get the coordinates of the reachable nodes
        reachable_coords = [(data['y'], data['x']) for node_id, data in reachable_nodes.items()]

        data = self.copernicus_raster['data']
        transform = self.copernicus_raster['transform']

        green_area_pixels = 0
        total_pixels = 0
        green_areas_info = {}

        for lat_point, lon_point in reachable_coords:
            try:
                # Convert coordinates to raster indices
                row, col = [int(i) for i in ~transform * (lon_point, lat_point)]


                if 0 <= row < data.shape[0] and 0 <= col < data.shape[1]:
                    total_pixels += 1
                    pixel_value = data[row, col]

                    # Update green area count
                    if pixel_value in GREEN_AREAS:
                        green_area_pixels += 1

                        category = self._get_green_area_category(pixel_value)
                        if category in green_areas_info:
                            green_areas_info[category] += 1
                        else:
                            green_areas_info[category] = 1
            except Exception:
                continue

        # Percentage of green area
        green_percentage = (green_area_pixels / max(1, total_pixels)) * 100

        # Copernicus raster resolution is 10m x 10m
        pixel_area_sqm = 100  # 10m x 10m
        green_area_sqm = green_area_pixels * pixel_area_sqm

        green_accessibility = {}
        for node_id, data in reachable_nodes.items():
            if node_id in G.nodes:
                node_coords = (data['y'], data['x'])
                try:
                    row, col = [int(i) for i in ~transform * (data['x'], data['y'])]
                    if 0 <= row < data.shape[0] and 0 <= col < data.shape[1]:
                        pixel_value = data[row, col]
                        if pixel_value in GREEN_AREAS:
                            time_to_node = data['time']
                            distance_meters = self._estimate_distance_from_time(time_to_node, network_type)
                            travel_time = self.calculate_travel_time(distance_meters, network_type)
                            category = self._get_green_area_category(pixel_value)
                            green_accessibility[node_id] = {
                                'category': category,
                                'time_minutes': travel_time,
                                'distance_meters': round(distance_meters, 2),
                                'lat': data['y'],
                                'lon': data['x']
                            }
                except Exception:
                    continue

        result = {
            "isochrone_time_minutes": max_time,
            "transport_mode": network_type,
            "green_area_percentage": round(green_percentage, 2),
            "green_area_sqm": round(green_area_sqm, 2),
            "green_area_categories": green_areas_info,
        }

        return json.dumps(result)



    def _get_green_area_category(self, pixel_value):
        categories = {
            10: "tree_cover",
            20: "shrubland",
            30: "grassland",
            60: "sparse_vegetation",
            95: "mangroves",
            100: "moss_lichen"
        }
        return categories.get(pixel_value, "unknown")

    def _estimate_distance_from_time(self, time_seconds, transport_mode):
        # Speed constants in m/s
        SPEEDS = {
            'walk': 5 / 3.6,
            'bike': 15 / 3.6,
            'car': 30 / 3.6,
            'bus': 20 / 3.6,
            'tram': 25 / 3.6,
            'metro': 50 / 3.6,
            'taxi': 30 / 3.6
        }

        # Delay factors
        DELAY_FACTORS = {
            'walk': 1.15,
            'bike': 1.2,
            'car': 1.25,
            'bus': 1.2,
            'tram': 1.15,
            'metro': 1.0,
            'taxi': 1.25
        }

        # Get values for the transport mode
        speed = SPEEDS.get(transport_mode, SPEEDS['walk'])
        delay_factor = DELAY_FACTORS.get(transport_mode, 1.0)

        distance = time_seconds * speed / delay_factor

        return distance