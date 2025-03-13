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

    def get_green_area(self, **kwargs):
        try:
            nodes_gdf, edges_gdf = self.osm
            if kwargs is None:
                green_tags = {
                    'natural': ['wood', 'tree_row', 'tree', 'scrub', 'grassland',
                                'heath', 'fell', 'tundra', 'shrubbery'],
                    'landuse': ['forest', 'meadow', 'grass','allotments'],
                    'leisure': ['park', 'garden', 'nature_reserve']
                }
            else :
                green_tags = kwargs.get('green_tags', {
                    'natural': ['wood', 'tree_row', 'tree', 'scrub', 'grassland',
                                'heath', 'fell', 'tundra', 'shrubbery'],
                    'landuse': ['forest', 'meadow', 'grass','allotments'],
                    'leisure': ['park', 'garden', 'nature_reserve']
                })

            def filter_green(df):
                if df.empty:
                    return df

                mask = pd.Series(False, index=df.index)

                for tag, values in green_tags.items():
                    if tag in df.columns:
                        mask |= df[tag].isin(values)

                return df[mask]

            # Optimized filtering
            green_nodes = filter_green(nodes_gdf)
            green_edges = filter_green(edges_gdf)

            return (green_nodes, green_edges)

        except Exception as e:
            return (pd.DataFrame(), pd.DataFrame())

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
