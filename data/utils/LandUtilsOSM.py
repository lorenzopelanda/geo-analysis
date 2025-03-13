import json
import geopandas as gpd
import osmnx as ox
import pandas as pd
from shapely.geometry import Polygon, MultiPolygon, LineString, MultiLineString, Point

from .UtilsInterface import UtilsInterface


class LandUtilsOSM(UtilsInterface):
    def __init__(self, osm, bounding_box):
        self.bounding_box = bounding_box
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

    def get_green_area(self):
        try:
            bounding_box = self.bounding_box
            aoi_box = bounding_box.to_geometry()

            print("Bounding box coordinates:", aoi_box.bounds)  # Debug

            green_tags = {
                'natural': ['wood', 'tree_row', 'tree', 'scrub', 'grassland', 'heath', 'fell', 'tundra', 'shrubbery'],
                'landuse': ['forest', 'meadow', 'grass', 'recreation_ground', 'village_green', 'allotments'],
                'leisure': ['park', 'garden', 'nature_reserve']
            }

            gdf = ox.features_from_polygon(aoi_box, tags=green_tags)

            print(f"{len(gdf)} green features found in the area")

            polygon_types = (Polygon, MultiPolygon)
            line_types = (LineString, MultiLineString)

            nodes = gdf[gdf.geometry.apply(lambda geom: isinstance(geom, Point))].copy()
            edges = gdf[gdf.geometry.apply(
                lambda geom: isinstance(geom, polygon_types + line_types)
            )].copy()
            print(f"{len(nodes)} node features")
            print(f"{len(edges)} edge/polygon features")

            return (nodes, edges)

        except Exception as e:
            print(f"Error extracting green areas: {str(e)}")
            return (pd.DataFrame(), pd.DataFrame())

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
