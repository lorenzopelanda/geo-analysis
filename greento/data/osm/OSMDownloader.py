import osmnx as ox
import geopandas as gpd
import warnings
from tqdm import tqdm
from shapely.geometry import Point, LineString, MultiLineString, Polygon, MultiPolygon
from greento.data.DataInterface import DownloaderInterface

class OSMDownloader(DownloaderInterface):

    def get_data(self, bounding_box):
        steps = ["Converting bounding box to geometry", "Downloading OSM data", "Filtering data"]
        with tqdm(total=100, desc="Overall Progress", unit="step") as pbar:
            pbar.set_description(steps[0])
            aoi_box = bounding_box.to_geometry()
            pbar.update(20)

            with warnings.catch_warnings():
                warnings.filterwarnings(
                    'ignore',
                    category=DeprecationWarning,
                    message='.*iloc.*'
                )

                try:
                    pbar.set_description(steps[1])
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
                    pbar.update(50)
                    if features.empty:
                        return (gpd.GeoDataFrame(), gpd.GeoDataFrame())
                    
                    point_mask = features.geometry.apply(lambda g: isinstance(g, Point))
                    poly_mask = features.geometry.apply(
                        lambda g: isinstance(g, (LineString, MultiLineString, Polygon, MultiPolygon))
                    )

                    nodes_gdf = features.loc[point_mask].copy()
                    edges_gdf = features.loc[poly_mask].copy()
                    pbar.update(30)
                    pbar.set_description("OSM data downloaded")

                    return (nodes_gdf, edges_gdf)

                except Exception as e:
                    raise ValueError(f"Error during OSM data download: {str(e)}")





