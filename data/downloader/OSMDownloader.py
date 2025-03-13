import osmnx as ox
import geopandas as gpd
import warnings
from shapely.geometry import Point, LineString, MultiLineString, Polygon, MultiPolygon
from data.utils.UtilsInterface import DownloaderInterface

class OSMDownloader(DownloaderInterface):

    def get_data(self, bounding_box):
        aoi_box = bounding_box.to_geometry()

        with warnings.catch_warnings():
            warnings.filterwarnings(
                'ignore',
                category=DeprecationWarning,
                message='.*iloc.*'
            )

            try:

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
                    return (gpd.GeoDataFrame(), gpd.GeoDataFrame())

                # Filtraggio ottimizzato
                point_mask = features.geometry.apply(lambda g: isinstance(g, Point))
                poly_mask = features.geometry.apply(
                    lambda g: isinstance(g, (LineString, MultiLineString, Polygon, MultiPolygon))
                )

                nodes_gdf = features.loc[point_mask].copy()
                edges_gdf = features.loc[poly_mask].copy()

                return (nodes_gdf, edges_gdf)

            except Exception as e:
                raise ValueError(f"Error during OSM data download: {str(e)}")





