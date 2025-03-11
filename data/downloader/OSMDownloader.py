import osmnx as ox
import geopandas as gpd
from data.utils.UtilsInterface import DownloaderInterface

class OSMDownloader(DownloaderInterface):
    # def get_data(self, bounding_box):
    #     aoi_box = bounding_box.to_geometry()
    #
    #     try:
    #         graph = ox.graph_from_polygon(aoi_box, custom_filter='')
    #         if graph is None:
    #             print("Failed to create graph")
    #             return None
    #         nodes,edges = ox.graph_to_gdfs(graph, nodes=True, edges=True)
    #         nodes = gpd.clip(nodes, aoi_box)
    #         edges = gpd.clip(edges, aoi_box)
    #         nodes['x'] = nodes.geometry.x
    #         nodes['y'] = nodes.geometry.y
    #         if nodes.empty or edges.empty:
    #             print("Warning: Empty nodes or edges after processing")
    #             return None
    #         return (nodes, edges)
    #     except Exception as e:
    #         print(f"Error processing OSM data: {str(e)}")
    #         raise
    def get_data(self, bounding_box):
        aoi_box = bounding_box.to_geometry()

        try:
            print("Bounding box coordinates:", aoi_box.bounds)  # Debug

            # Scarica il grafo senza filtri
            graph = ox.graph_from_polygon(aoi_box)

            if graph is None or len(graph.nodes) == 0:
                print("Failed to create graph or graph is empty")
                return None

            print(len(graph.nodes), "nodes in graph")
            print(len(graph.edges), "edges in graph")

            nodes = ox.graph_to_gdf(graph, nodes=True)  # Nodi come GeoDataFrame
            edges = ox.graph_to_gdf(graph, nodes=False) # Convertire solo gli archi in GeoDataFrame

            return (nodes, edges)

        except Exception as e:
            print(f"Error processing OSM data: {str(e)}")
            raise



