import osmnx as ox
import geopandas as gpd
import warnings
import pandas as pd
from shapely.geometry import Point, LineString, MultiLineString, Polygon, MultiPolygon
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

        with warnings.catch_warnings():
            warnings.filterwarnings(
                'ignore',
                category=DeprecationWarning,
                message='.*iloc.*'
            )

            try:
                print("Bounding box coordinates:", aoi_box.bounds)

                features = ox.features_from_polygon(
                    aoi_box,
                    tags={
                        "natural": True,
                        "landuse": True,
                        "leisure": True,
                        "highway": True,
                        "building": True,
                        "waterway": True,
                        "water": True
                    }
                )

                if features.empty:
                    print("No features found")
                    return (gpd.GeoDataFrame(), gpd.GeoDataFrame())

                # Filtraggio ottimizzato
                point_mask = features.geometry.apply(lambda g: isinstance(g, Point))
                poly_mask = features.geometry.apply(
                    lambda g: isinstance(g, (LineString, MultiLineString, Polygon, MultiPolygon))
                )

                nodes_gdf = features.loc[point_mask].copy()
                edges_gdf = features.loc[poly_mask].copy()

                print(f"{len(nodes_gdf)} nodes, {len(edges_gdf)} polygons")

                return (nodes_gdf, edges_gdf)

            except Exception as e:
                print(f"Error: {str(e)}")
                return (gpd.GeoDataFrame(), gpd.GeoDataFrame())




