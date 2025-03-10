import osmnx as ox
import geopandas as gpd
from data.utils.UtilsInterface import DownloaderInterface

class OSMDownloader(DownloaderInterface):
    def get_data(self, bounding_box):
        aoi_box = bounding_box.to_geometry()

        try:
            graph = ox.graph_from_polygon(aoi_box, custom_filter='')
            if graph is None:
                print("Failed to create graph")
                return None
            nodes,edges = ox.graph_to_gdfs(graph, nodes=True, edges=True)
            nodes = gpd.clip(nodes, aoi_box)
            edges = gpd.clip(edges, aoi_box)
            nodes['x'] = nodes.geometry.x
            nodes['y'] = nodes.geometry.y
            if nodes.empty or edges.empty:
                print("Warning: Empty nodes or edges after processing")
                return None
            return (nodes, edges)
        except Exception as e:
            print(f"Error processing OSM data: {str(e)}")
            raise

    def get_vector_area(self, bounding_box, tags):
        nodes, edges = self.get_data(bounding_box)

        try:
            if nodes is None or edges is None:
                return gpd.GeoDataFrame()

            for key, values in tags.items():
                nodes = nodes[nodes[key].isin(values)]
                edges = edges[edges[key].isin(values)]

            return nodes, edges

        except Exception as e:
            print(f"Error extracting OSM tags: {str(e)}")
            raise


    def get_traffic_area(self, bounding_box, network_type):
        """
        Download the OSM network data for a given bounding box and network type, and rasterize it to a reference raster.
        """

        try:
            nodes, edges = self.get_data(bounding_box)
            if nodes is None or edges is None:
                return None

            # Filter nodes and edges based on the network type
            filtered_nodes = nodes[nodes['highway'].isin([network_type])]
            filtered_edges = edges[edges['highway'].isin([network_type])]

            if filtered_nodes.empty or filtered_edges.empty:
                print("Warning: Empty nodes or edges after processing")
                return None

            return (filtered_nodes, filtered_edges)

        except Exception as e:
            print(f"Error processing OSM data: {str(e)}")
            raise
