import json
import geopandas as gpd
from .UtilsInterface import UtilsInterface


class LandUtilsOSM(UtilsInterface):
    def __init__(self, osm):
        self.osm = osm

    def get_land_use_percentages(self):
        nodes, edges = self.osm
        if nodes is None or edges is None:
            return json.dumps({})
        land_use_types = nodes['natural'].value_counts().to_dict()
        total = sum(land_use_types.values())
        percentages = {key: round((count / total) * 100, 4) for key, count in land_use_types.items()}
        return json.dumps(percentages)

    # def get_green_area(self,**kwargs):
    #     nodes, edges = self.osm
    #     green_tags = {
    #         'natural': ['fell', 'natural', 'grassland', 'heath', 'scrub', 'tree', 'wood',
    #                     'shrubbery', 'tree_row', 'tundra']
    #     }
    #     try:
    #         if kwargs:
    #             green_tags = kwargs
    #
    #         green_nodes = nodes[nodes['natural'].isin(green_tags.get('natural', []))]
    #         green_edges = edges[edges['natural'].isin(green_tags.get('natural', []))]
    #
    #         if green_nodes.empty or green_edges.empty:
    #             print("No green areas found in the bounding box")
    #             return None
    #
    #         return (green_nodes, green_edges)
    #     except Exception as e:
    #         print(f"Error processing OSM green areas: {str(e)}")
    #         raise

    def get_green_area(self, **kwargs):
        nodes, edges = self.osm
        green_tags = {
            'natural': ['fell', 'natural', 'grassland', 'heath', 'scrub', 'tree', 'wood',
                        'shrubbery', 'tree_row', 'tundra']
        }

        try:
            if kwargs:
                green_tags = kwargs

            # Verifica se la colonna 'natural' esiste
            if 'natural' not in nodes.columns:
                print("Warning: 'natural' column not found in nodes")
                return None
            if 'natural' not in edges.columns:
                print("Warning: 'natural' column not found in edges")
                return None

            green_nodes = nodes[nodes['natural'].isin(green_tags.get('natural', []))]
            green_edges = edges[edges['natural'].isin(green_tags.get('natural', []))]

            if green_nodes.empty or green_edges.empty:
                print("No green areas found in the bounding box")
                return None

            return (green_nodes, green_edges)
        except Exception as e:
            print(f"Error processing OSM green areas: {str(e)}")
            raise

    def get_vector_area(self,tags):
        nodes, edges = self.osm

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


    def get_traffic_area(self, network_type):
        """
        Download the OSM network data for a given bounding box and network type, and rasterize it to a reference raster.
        """

        try:
            nodes, edges = self.osm
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
