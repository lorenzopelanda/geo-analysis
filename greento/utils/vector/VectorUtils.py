import json
import osmnx as ox
import pandas as pd
import numpy as np
import geopandas as gpd
from tqdm import tqdm
from rasterio.features import rasterize 
from greento.utils.UtilsInterface import UtilsInterface

class VectorUtils(UtilsInterface):
    """
    A class to provide utility functions for processing vector data.

    Attributes:
    ----------
    osm : tuple
        A tuple containing two GeoDataFrames: nodes and edges.

    Methods:
    -------
    get_land_use_percentages():
        Calculates the land use percentages from the OSM data.
    to_raster(vector_data, reference_raster):
        Rasterizes the OpenStreetMap vector data using a reference raster.
    """
    def __init__(self, osm):
        """
        Initializes the VectorUtils with OSM data.

        Parameters:
        ----------
        osm : tuple
            A tuple containing two GeoDataFrames: nodes and edges.
        """
        self.osm = osm
        
    def get_land_use_percentages(self):
        """
        Calculates the land use percentages from the OSM data.

        Returns:
        -------
        str
            A JSON string containing the land use percentages.
        """
        nodes, edges = self.osm
        if nodes is None or edges is None:
            return json.dumps({})
        land_use_types = nodes['natural'].value_counts().to_dict()
        total = sum(land_use_types.values())
        percentages = {key: round((count / total) * 100, 4) for key, count in land_use_types.items()}
        return json.dumps(percentages)
    
    def to_raster(self, reference_raster):
        """
        Rasterizes the OpenStreetMap vector data using a reference raster.

        Parameters:
        ----------
        reference_raster : dict
            Reference raster containing 'data', 'transform', 'crs', and 'shape'.

        Returns:
        -------
        dict
            Rasterized output with 'data', 'transform', 'crs', and 'shape'.
        """
        nodes, edges = self.osm
        ref_crs = reference_raster['crs']

        if not isinstance(nodes, gpd.GeoDataFrame) or 'geometry' not in nodes.columns:
            raise ValueError("Nodes must be a GeoDataFrame and contain a 'geometry' column")
        if not isinstance(edges, gpd.GeoDataFrame) or 'geometry' not in edges.columns:
            raise ValueError("Edges must be a GeoDataFrame and contain a 'geometry' column")

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