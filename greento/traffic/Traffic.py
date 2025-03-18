import osmnx as ox
import geopandas as gpd
from tqdm import tqdm

class Traffic:
    def __init__(self, bounding_box):
        self.bounding_box = bounding_box

    def get_traffic_area(self, network_type):
        """
        Download the OSM network data for a given bounding box and network type, and rasterize it to a reference raster.
        """
        bounding_box = self.bounding_box
        aoi_box = bounding_box.to_geometry()
        with tqdm(total = 100, desc= "Downloading traffic data") as pbar:
            pbar.update(10)
            # Download traffic network
            graph = ox.graph_from_polygon(aoi_box, network_type=network_type, simplify=True)
            pbar.update(40)
            pbar.set_description("Processing traffic data")

            if graph is None:
                print("Failed to create graph")
                return None

            # Convert graph to GeoDataFrames
            nodes, edges = ox.graph_to_gdfs(graph, nodes=True, edges=True)
            pbar.update(20)
            # Clip to AOI
            nodes = gpd.clip(nodes, aoi_box)
            pbar.update(10)
            edges = gpd.clip(edges, aoi_box)
            pbar.update(10)
            # Add coordinates
            nodes['x'] = nodes.geometry.x
            nodes['y'] = nodes.geometry.y

            if nodes.empty or edges.empty:
                print("Warning: Empty nodes or edges after processing")
                return None
            
            pbar.update(10)
            pbar.set_description("Finished obtaining traffic data")

        return (nodes, edges)
