import json
import numpy as np
import osmnx as ox
from MetricsInterface import MetricsInterface
from greento.utils.GeoUtils import Utils

class MetricsOSM(MetricsInterface):
    def __init__(self, osm, vector_traffic_area, ghs_pop_data):
        self.osm_file = osm
        self.vector_traffic_area = vector_traffic_area
        self.ghs_pop_data = ghs_pop_data

    def green_area_per_person(self):
        """
        Calculate the green area per person in the given raster and population data.
        """
        ghspop_data = self.ghs_pop_data['data']
        green_data = self.osm_green['data']

        num_green_pixels = np.count_nonzero(green_data)

        total_green_area = num_green_pixels * 100  # sqm

        total_population = np.sum(ghspop_data)

        if total_population == 0:
            return json.dumps({'green_area_per_person': float('inf')})
        else:
            green_area_per_person = round(total_green_area / total_population, 4)
            return json.dumps({'green_area_per_person': green_area_per_person})
    
    def get_isochrone_green(self, lat, lon, max_time, network_type):
        """
        Calculate the reachable green areas within a given time from a starting point.
        """
        if not (isinstance(lat, (int, float)) and isinstance(lon, (int, float))):
            raise ValueError("Coordinates not valid")

        if not isinstance(max_time, (int, float)) or max_time <= 0:
            raise ValueError("Max time not valid")

        valid_transport_modes = ['walk', 'bike', 'drive', 'all_public', 'drive_public']
        if network_type not in valid_transport_modes:
            raise ValueError(f"Transport mode not valid. Choose from: {', '.join(valid_transport_modes)}")

        if not hasattr(self, 'vector_traffic_area') or self.vector_traffic_area is None:
            raise ValueError("Traffic area not reachable")

        speed_kmh = {
            'walk': 5,
            'bike': 15,
            'drive': 30,
            'all_public': 30,
            'drive_public': 30
        }.get(network_type, 5)

        nodes, edges = self.vector_traffic_area
        G = ox.graph_from_gdfs(nodes, edges)  # Ristructure of the graph
        # Find nearest node from starting point
        start_node, _ = ox.distance.nearest_nodes(G, X=lon, Y=lat, return_dist=True)

        FIXED_DELAYS = {
            'walk': 0,
            'bike': 30,  # take/return bike
            'drive': 180,  # parking + take the car
            'all_public': 420,  # walk to the stop (3 min) + estimated wait (4 min)
            'drive_public': 180  # wait + call
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
                length_m = data['length']
                data['travel_time'] = length_m / (speed_kmh * 1000 / 3600)

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

        data = self.osm_green['data']
        transform = self.osm_green['transform']

        total_pixels = 0
        green_area_pixels = 0
        green_accessibility = {}

        for lat_point, lon_point in reachable_coords:
            try:
                # Convert coordinates to raster indices
                row, col = [int(i) for i in ~transform * (lon_point, lat_point)]

                if 0 <= row < data.shape[0] and 0 <= col < data.shape[1]:
                    total_pixels += 1
                    pixel_value = data[row, col]

                    # Count every pixel as green area
                    if pixel_value == 1:
                        green_area_pixels += 1

                        node_data = next(
                            (d for n, d in reachable_nodes.items() if d['y'] == lat_point and d['x'] == lon_point),
                            None)
                        if node_data:
                            time_to_node = node_data['time']
                            distance_meters = self._estimate_distance_from_time(time_to_node, network_type)
                            travel_time = Utils()._calculate_travel_time(distance_meters, network_type)
                            green_accessibility[node_data['x']] = {
                                'time_minutes': travel_time,
                                'distance_meters': round(distance_meters, 2),
                                'lat': lat_point,
                                'lon': lon_point
                            }
            except Exception:
                continue

        green_percentage = (green_area_pixels / max(1, total_pixels)) * 100 if total_pixels > 0 else 0

        pixel_area_sqm = 100  # 10m x 10m
        green_area_sqm = green_area_pixels * pixel_area_sqm

        result = {
            "isochrone_time_minutes": max_time,
            "transport_mode": network_type,
            "green_area_percentage": round(green_percentage, 2),
            "green_area_sqm": round(green_area_sqm, 2),
            "green_accessibility": list(green_accessibility.values()),
        }

        return json.dumps(result)

    def _estimate_distance_from_time(self, time_seconds, transport_mode):
        # Speed constants in m/s
        SPEEDS = {
            'walk': 5 / 3.6,
            'bike': 15 / 3.6,
            'drive': 30 / 3.6,
            'all_public': 30 / 3.6,
            'drive_public': 30 / 3.6
        }

        # Delay factors
        DELAY_FACTORS = {
            'walk': 1.15,
            'bike': 1.2,
            'drive': 1.25,
            'all_public': 1.10,
            'drive_public': 1.25
        }

        # Get values for the transport mode
        speed = SPEEDS.get(transport_mode, SPEEDS['walk'])
        delay_factor = DELAY_FACTORS.get(transport_mode, 1.0)

        distance = time_seconds * speed / delay_factor

        return distance