import osmnx as ox
import geopandas as gpd
import warnings
import logging
from tqdm import tqdm
from shapely.geometry import Point, LineString, MultiLineString, Polygon, MultiPolygon
from src.greento.boundingbox import boundingbox
from src.greento.data.interface import interface

class osm(interface):
    """
    A class to download and process OpenStreetMap (OSM) data.

    Methods
    -------
    get_data(bounding_box: "boundingbox") -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]
        Downloads and processes OSM data for the given bounding box.
    """

    def get_data(self, bounding_box: "boundingbox") -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
        """
        Downloads and processes OSM data for the given bounding box.

        Parameters
        ----------
        bounding_box : boundingbox
            The bounding box for which to download data.

        Returns
        -------
        tuple
            A tuple containing two GeoDataFrames:
            - nodes (geopandas.GeoDataFrame): GeoDataFrame containing point features (e.g., nodes).
            - edges (geopandas.GeoDataFrame): GeoDataFrame containing line and polygon features (e.g., edges).

        Raises
        ------
        ValueError
            If an error occurs during the OSM data download or processing.

        Notes
        -----
        The method uses the `osmnx` library to fetch OSM data and filters it into nodes and edges based on geometry types.
        """
        steps = ["Converting bounding box to geometry", "Downloading OSM data", "Filtering data"]
        with tqdm(total=100, desc="Overall Progress", unit="step", leave=False) as pbar:
            pbar.set_description(steps[0])
            aoi_box = bounding_box.to_geometry()
            pbar.update(20)

            with warnings.catch_warnings():
                warnings.filterwarnings(
                    'ignore',
                    category=DeprecationWarning,
                    message='.*iloc.*'
                )

                logger = logging.getLogger(__name__)
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
                    pbar.close()
                    return (nodes_gdf, edges_gdf)

                except Exception as e:
                    logger.error(f"Error during OSM data download: {str(e)}")




