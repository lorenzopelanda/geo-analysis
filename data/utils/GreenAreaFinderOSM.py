import rasterio
import numpy as np
import json
import osmnx as ox
import geopandas as gpd
from shapely.geometry import Point
from scipy.spatial import cKDTree
from .UtilsInterface import GreenInterface
ox.settings.use_cache = True

class GreenAreaFinderOSM(GreenInterface):
    def __init__(self, osm_green, vector_traffic_area, ghs_pop_data):
        self.vector_green = osm_green
        self.vector_traffic_area = vector_traffic_area
        self.preprocessed_graph = None
        self.ghs_pop_data = ghs_pop_data
        self._green_positions_cache = {}

    def _calculate_travel_time(self, distance_meters, transport_mode):
        """
        Calculate the estimated travel time for a given distance and transport mode.
        """
        # Speed constants in km/h
        SPEEDS = {
            'walk': 1.4,  # 5 km/h
            'bike': 4.17,  # 15 km/h
            'drive': 8.33,  # 30 km/h (urban)
            'all_public': 8.33, # 30 km/h
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

    def green_area_per_person(self):
        green_nodes, green_edges = self.vector_green

        ghspop_data = self.ghs_pop_data['data']
        total_population = np.sum(ghspop_data)

        # Calculate total green area in square meters
        total_green_area = 0.0

        # Calculate area from green edges (polygons)
        if not green_edges.empty:
            for _, edge in green_edges.iterrows():
                if hasattr(edge, 'geometry') and edge.geometry is not None:
                    total_green_area += edge.geometry.area

        # Per i nodi (punti come alberi singoli), assegniamo un'area standard stimata
        if not green_nodes.empty:
            standard_node_area = 10.0  # Ad esempio, 10 mq per un albero
            total_green_area += len(green_nodes) * standard_node_area

        # Return green area per person
        if total_population == 0:
            return float('inf')
        else:
            return round(total_green_area / total_population, 4)

    def get_nearest_green_position(self, lat, lon):
        """
        Find the nearest green area to the given coordinates using OpenStreetMap vector data.

        Args:
            lat (float): Latitude of the point
            lon (float): Longitude of the point

        Returns:
            tuple: (latitude, longitude) of the nearest green area
        """
        # Validate coordinates
        if not (isinstance(lat, (int, float)) and isinstance(lon, (int, float))):
            raise ValueError("Coordinate non valide")

        # Get green areas from OSM data
        green_nodes, green_edges = self.vector_green['data']

        # Create a point from input coordinates
        point = Point(lon, lat)
        user_point = gpd.GeoDataFrame(geometry=[point], crs="EPSG:4326")

        # Check if the point is already in a green area
        if not green_edges.empty:
            # Check if point is within any green edge/polygon
            is_in_green = False
            for _, edge in green_edges.iterrows():
                if hasattr(edge, 'geometry') and edge.geometry is not None:
                    if edge.geometry.contains(point):
                        return lat, lon

        # Prepare nodes for distance calculation
        if not green_nodes.empty:
            # Extract coordinates from green nodes
            green_points = []
            for _, node in green_nodes.iterrows():
                if hasattr(node, 'geometry') and node.geometry is not None:
                    green_points.append((node.geometry.y, node.geometry.x))  # (lat, lon)

            if not green_points:
                raise ValueError("No valid green points found")

            # Create KDTree for efficient nearest neighbor search
            tree = cKDTree(green_points)

            # Find nearest point
            dist, idx = tree.query((lat, lon), k=1)
            nearest_point = green_points[idx]

            return nearest_point  # Returns (lat, lon)

        # If we have edges but no nodes, use edge centroids
        if not green_edges.empty and green_nodes.empty:
            centroids = []
            for _, edge in green_edges.iterrows():
                if hasattr(edge, 'geometry') and edge.geometry is not None:
                    centroid = edge.geometry.centroid
                    centroids.append((centroid.y, centroid.x))  # (lat, lon)

            if not centroids:
                raise ValueError("No green edges with valid geometry found")

            # Create KDTree for efficient nearest neighbor search
            tree = cKDTree(centroids)

            # Find nearest point
            dist, idx = tree.query((lat, lon), k=1)
            nearest_point = centroids[idx]

            return nearest_point  # Returns (lat, lon)
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

    def get_isochrone_green(self, lat, lon, max_time, network_type):
        """
        Calculate the reachable green areas within a given time from a starting point
        using OSM vector data instead of raster data.

        Args:
            lat (float): Latitude of starting point
            lon (float): Longitude of starting point
            max_time (int/float): Maximum travel time in minutes
            network_type (str): Type of transportation network

        Returns:
            str: JSON string with information about reachable green areas
        """
        import json
        import geopandas as gpd
        from shapely.geometry import Point, Polygon
        import numpy as np
        import osmnx as ox

        if not (isinstance(lat, (int, float)) and isinstance(lon, (int, float))):
            raise ValueError("Coordinates not valid")

        if not isinstance(max_time, (int, float)) or max_time <= 0:
            raise ValueError("Max time not valid")

        valid_transport_modes = ['walk', 'bike', 'drive', 'all_public', 'drive_public']
        if network_type not in valid_transport_modes:
            raise ValueError(f"Transport mode not valid. Choose from: {', '.join(valid_transport_modes)}")

        # Get green areas using the get_green_area method
        green_data = self.get_green_area()
        if green_data is None:
            return json.dumps({"error": "No green areas found in the region"})

        green_nodes, green_edges = green_data

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
        G = ox.graph_from_gdfs(nodes, edges)  # Restructure of the graph

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

        # Calculate travel time for each edge
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
            return json.dumps({"error": "No reachable nodes for the time limit"})

        # Create a GeoDataFrame from reachable nodes
        reachable_points = []
        for node_id, data in reachable_nodes.items():
            reachable_points.append(Point(data['x'], data['y']))

        reachable_gdf = gpd.GeoDataFrame(geometry=reachable_points, crs="EPSG:4326")

        # Try to create a convex hull or concave hull to represent the isochrone area
        # Simplifying by using convex hull for this example
        if len(reachable_points) >= 3:
            isochrone_polygon = Polygon([(p.x, p.y) for p in reachable_points]).convex_hull
        else:
            # Not enough points for a polygon, use a buffer around points
            isochrone_polygon = reachable_gdf.unary_union.buffer(0.001)  # Small buffer in degrees

        isochrone_gdf = gpd.GeoDataFrame(geometry=[isochrone_polygon], crs="EPSG:4326")

        # Calculate intersection with green areas
        green_area_total = 0
        green_areas_info = {}
        green_accessibility = {}

        # Calculate total isochrone area
        isochrone_area = isochrone_polygon.area

        # Process green edges (polygons/lines)
        if not green_edges.empty:
            # Make sure CRS matches
            if green_edges.crs != isochrone_gdf.crs:
                green_edges = green_edges.to_crs(isochrone_gdf.crs)

            # Find intersection
            intersecting_greens = gpd.overlay(green_edges, isochrone_gdf, how='intersection')

            if not intersecting_greens.empty:
                for idx, green in intersecting_greens.iterrows():
                    if hasattr(green, 'geometry') and green.geometry is not None:
                        area = green.geometry.area
                        green_area_total += area

                        # Categorize green areas - using natural tag as category
                        category = green.get('natural', 'unknown')
                        if category in green_areas_info:
                            green_areas_info[category] += area
                        else:
                            green_areas_info[category] = area

        # Process green nodes (points)
        if not green_nodes.empty:
            # Make sure CRS matches
            if green_nodes.crs != isochrone_gdf.crs:
                green_nodes = green_nodes.to_crs(isochrone_gdf.crs)

            # Standard area for node features (e.g., trees)
            standard_node_area = 10.0  # 10 sq meters for a tree

            # Find nodes within isochrone
            nodes_within = gpd.sjoin(green_nodes, isochrone_gdf, predicate='within')

            if not nodes_within.empty:
                node_count = len(nodes_within)
                node_area_total = node_count * standard_node_area
                green_area_total += node_area_total

                # Group by category
                for category, group in nodes_within.groupby('natural'):
                    count = len(group)
                    area = count * standard_node_area
                    if category in green_areas_info:
                        green_areas_info[category] += area
                    else:
                        green_areas_info[category] = area

        # Calculate percentage of green area within isochrone
        # Convert area to square meters
        # Since we're using EPSG:4326, we need to approximate the area in sq meters
        # This is a rough approximation - for precision, a projected CRS would be better
        isochrone_area_sqm = isochrone_area * 111320 * 111320  # rough conversion from degrees to meters
        green_percentage = (green_area_total / max(0.000001, isochrone_area_sqm)) * 100

        # Identify accessible green areas with travel times
        for node_id, data in reachable_nodes.items():
            node_point = Point(data['x'], data['y'])

            # Check green edges
            if not green_edges.empty:
                for idx, green in green_edges.iterrows():
                    if green.geometry.contains(node_point) or green.geometry.distance(node_point) < 0.0001:
                        time_to_node = data['time']
                        distance_meters = self._estimate_distance_from_time(time_to_node, network_type)
                        travel_time = self._calculate_travel_time(distance_meters, network_type)
                        category = self._get_green_area_category_osm(green)

                        green_accessibility[node_id] = {
                            'category': category,
                            'time_minutes': travel_time,
                            'distance_meters': round(distance_meters, 2),
                            'lat': data['y'],
                            'lon': data['x']
                        }
                        break

            # Check green nodes
            if not green_nodes.empty and node_id not in green_accessibility:
                for idx, green_node in green_nodes.iterrows():
                    green_point = green_node.geometry
                    if node_point.distance(green_point) < 0.0001:  # Close enough
                        time_to_node = data['time']
                        distance_meters = self._estimate_distance_from_time(time_to_node, network_type)
                        travel_time = self._calculate_travel_time(distance_meters, network_type)
                        category = self._get_green_area_category_osm(green)

                        green_accessibility[node_id] = {
                            'category': category,
                            'time_minutes': travel_time,
                            'distance_meters': round(distance_meters, 2),
                            'lat': data['y'],
                            'lon': data['x']
                        }
                        break

        # Round values in green_areas_info
        green_areas_info = {k: round(v, 2) for k, v in green_areas_info.items()}

        result = {
            "isochrone_time_minutes": max_time,
            "transport_mode": network_type,
            "green_area_percentage": round(green_percentage, 2),
            "green_area_sqm": round(green_area_total, 2),
            "green_area_categories": green_areas_info,
            "accessibility": green_accessibility
        }

        return json.dumps(result)

    def _get_green_area_category_osm(self, feature):
        green_tags = {
            'natural': ['fell', 'natural', 'grassland', 'heath', 'scrub', 'tree', 'wood',
                        'shrubbery', 'tree_row', 'tundra']
        }
        if hasattr(feature, 'natural') and feature.natural in green_tags.get('natural', []):
            return feature.natural

        # Could extend with additional tag checks if needed
        # For example, if you also use 'landuse' tags for green areas:
        # if hasattr(feature, 'landuse') and feature.landuse in self.green_tags.get('landuse', []):
        #     return feature.landuse

        return "unknown"
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