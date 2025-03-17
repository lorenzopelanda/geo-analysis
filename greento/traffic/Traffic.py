import osmnx as ox
import geopandas as gpd

class Traffic:
    def __init__(self, osm, bounding_box):
        self.bounding_box = bounding_box
        self.osm = osm    

    def get_traffic_area(self, network_type):
        """
        Download the OSM network data for a given bounding box and network type, and rasterize it to a reference raster.
        """
        bounding_box = self.bounding_box
        aoi_box = bounding_box.to_geometry()

        graph = ox.graph_from_polygon(aoi_box, network_type=network_type, simplify=True)

        if graph is None:
            print("Failed to create graph")
            return None

        # Convert graph to GeoDataFrames
        nodes, edges = ox.graph_to_gdfs(graph, nodes=True, edges=True)
        # Clip to AOI
        nodes = gpd.clip(nodes, aoi_box)
        edges = gpd.clip(edges, aoi_box)
        # Add coordinates
        nodes['x'] = nodes.geometry.x
        nodes['y'] = nodes.geometry.y

        if nodes.empty or edges.empty:
            print("Warning: Empty nodes or edges after processing")
            return None

        return (nodes, edges)