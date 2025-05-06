import osmnx as ox
import geopandas as gpd
import logging
from tqdm import tqdm
from typing import Tuple, Optional
from greento.boundingbox import boundingbox


class traffic:
    """
    A class to download and process traffic data using OpenStreetMap (OSM) data.

    Attributes
    ----------
    bounding_box : BoundingBox
        The bounding box for which to download traffic data.

    Methods
    -------
    get_traffic_area(network_type: str) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]
        Downloads the OSM network data for a given bounding box and network type, and processes it into GeoDataFrames.
    """

    def __init__(self, bounding_box: "boundingbox") -> None:
        """
        Initializes the Traffic class with a bounding box.

        Parameters
        ----------
        bounding_box : BoundingBox
            The bounding box for which to download traffic data.

        Returns
        -------
        None
        """
        self.bounding_box = bounding_box

    def get_traffic_area(
        self, network_type: str
    ) -> Optional[Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]]:
        """
        Downloads the OSM network data for a given bounding box and network type, and processes it into GeoDataFrames.

        Parameters
        ----------
        network_type : str
            The type of transport network (e.g., 'walk', 'bike', 'drive', 'all', 'all_private', 'all_public').

        Returns
        -------
        tuple
            A tuple containing two GeoDataFrames:
            - nodes (geopandas.GeoDataFrame): GeoDataFrame containing the nodes of the traffic network.
            - edges (geopandas.GeoDataFrame): GeoDataFrame containing the edges of the traffic network.

        Raises
        ------
        RuntimeError
            If the graph creation fails or if the resulting nodes or edges are empty.

        Notes
        -----
        The method uses the `osmnx` library to fetch and process OSM traffic data.
        """
        bounding_box = self.bounding_box
        aoi_box = bounding_box.to_geometry()
        with tqdm(total=100, desc="Downloading traffic data", leave=False) as pbar:
            pbar.update(10)
            graph = ox.graph_from_polygon(
                aoi_box, network_type=network_type, simplify=True
            )
            pbar.update(40)
            pbar.set_description("Processing traffic data")

            if graph is None:
                logger = logging.getLogger(__name__)
                logger.error("Failed to create graph from bounding box")
                return None

            nodes, edges = ox.graph_to_gdfs(graph, nodes=True, edges=True)
            pbar.update(20)
            nodes = gpd.clip(nodes, aoi_box)
            pbar.update(10)
            edges = gpd.clip(edges, aoi_box)
            pbar.update(10)

            nodes["x"] = nodes.geometry.x
            nodes["y"] = nodes.geometry.y

            if nodes.empty or edges.empty:
                logger = logging.getLogger(__name__)
                logger.warning("Empty nodes or edges after processing")
                return None

            pbar.update(10)
            pbar.set_description("Finished obtaining traffic data")
            pbar.close()

        return (nodes, edges)
