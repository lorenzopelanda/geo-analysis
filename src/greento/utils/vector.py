import json
import osmnx as ox
import pandas as pd
import numpy as np
import geopandas as gpd
import logging
from tqdm import tqdm
from typing import Tuple
from rasterio.features import rasterize 
from greento.utils.interface import interface

class vector(interface):
    """
    A class to provide utility functions for processing vector data.

    Attributes
    ----------
    osm : tuple
        A tuple containing two GeoDataFrames: nodes and edges.

    Methods
    -------
    get_land_use_percentages() -> str
        Calculates the land use percentages from the OSM data.
    to_raster(reference_raster: dict) -> dict
        Rasterizes the OpenStreetMap vector data using a reference raster.
    """
    def __init__(self, osm: Tuple) -> None:
        """
        Initializes the VectorUtils with OSM data.

        Parameters
        ----------
        osm : tuple
            A tuple containing two GeoDataFrames: nodes and edges.

        Returns
        -------
        None
        """
        self.osm = osm
        
    def get_land_use_percentages(self) -> str:
        """
        Calculates the land use percentages from the OSM data.

        Returns
        -------
        str
            A JSON string containing the land use percentages, where keys are land use types and values are percentages.

        Raises
        ------
        ValueError
            If the OSM data is not available or does not contain the required columns.
        """
        nodes, edges = self.osm
        if nodes is None or edges is None:
            logger = logging.getLogger(__name__)
            logger.error("OSM data is not available.")
            return None
        land_use_types = nodes['natural'].value_counts().to_dict()
        total = sum(land_use_types.values())
        percentages = {key: round((count / total) * 100, 4) for key, count in land_use_types.items()}
        return json.dumps(percentages)
    
    def to_raster(self, reference_raster: dict) -> dict:
        """
        Rasterizes the OpenStreetMap vector data using a reference raster.

        Parameters
        ----------
        reference_raster : dict
            A dictionary containing the reference raster with the following keys:
                - 'data': The raster data.
                - 'transform': The affine transform of the raster.
                - 'crs': The coordinate reference system of the raster.
                - 'shape': The shape of the raster.

        Returns
        -------
        dict
            A dictionary containing the rasterized output with the following keys:
                - 'data': The rasterized data.
                - 'transform': The affine transform of the raster.
                - 'crs': The coordinate reference system of the raster.
                - 'shape': The shape of the raster.

        Raises
        ------
        ValueError
            If the nodes or edges are not valid GeoDataFrames or do not contain a 'geometry' column.
        """
        nodes, edges = self.osm
        ref_crs = reference_raster['crs']

        if not isinstance(nodes, gpd.GeoDataFrame) or 'geometry' not in nodes.columns:
            logger = logging.getLogger(__name__)
            logger.error("Nodes must be a GeoDataFrame and contain a 'geometry' column")
            return None
        if not isinstance(edges, gpd.GeoDataFrame) or 'geometry' not in edges.columns:
            logger = logging.getLogger(__name__)
            logger.error("Edges must be a GeoDataFrame and contain a 'geometry' column")
            return None

        with tqdm(total=100, desc="Rasterizing OSM data", leave=False) as pbar:
            node_shapes = [(geom, 1) for geom in nodes.geometry if geom is not None]
            node_rasterized = rasterize(
                shapes=node_shapes,
                out_shape=reference_raster['shape'],
                transform=reference_raster['transform'],
                fill=0,
                dtype=np.uint8,
                all_touched=True
            )
            pbar.update(40)

            edge_shapes = [(geom, 1) for geom in edges.geometry if geom is not None]
            edge_rasterized = rasterize(
                shapes=edge_shapes,
                out_shape=reference_raster['shape'],
                transform=reference_raster['transform'],
                fill=0,
                dtype=np.uint8,
                all_touched=True
            )
            pbar.update(40)

            combined_raster = np.maximum(node_rasterized, edge_rasterized)  
            pbar.update(20)
            pbar.set_description("Finished rasterizing OSM data")
            pbar.close()
            return {
                "data": combined_raster,
                "transform": reference_raster['transform'],
                "crs": ref_crs,
                "shape": reference_raster['shape']
            }