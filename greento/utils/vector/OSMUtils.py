import json
import osmnx as ox
import pandas as pd
import numpy as np
from rasterio.features import rasterize 
from greento.utils import UtilsInterface

class OSMUtils(UtilsInterface):
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
    
    def to_raster(self, vector_data, reference_raster):
        """
        Rasterize the OpenStreetMap vector data using a reference raster.

        Args:
            vector_data (tuple): A tuple containing nodes (GeoDataFrame of point data) and edges (GeoDataFrame of line/polygon data).
            reference_raster (dict): Reference raster containing 'data', 'transform', 'crs', and 'shape'.

        Returns:
            dict: Rasterized output with 'data', 'transform', 'crs', and 'shape'.
        """
        nodes, edges = vector_data
        ref_crs = reference_raster['crs']

        # Rasterize nodes (points)
        node_shapes = [(geom, 1) for geom in nodes.geometry if geom is not None]
        node_rasterized = rasterize(
            shapes=node_shapes,
            out_shape=reference_raster['shape'],
            transform=reference_raster['transform'],
            fill=0,
            dtype=np.uint8,
            all_touched=True
        )

        # Rasterize edges (lines or polygons)
        edge_shapes = [(geom, 1) for geom in edges.geometry if geom is not None]
        edge_rasterized = rasterize(
            shapes=edge_shapes,
            out_shape=reference_raster['shape'],
            transform=reference_raster['transform'],
            fill=0,
            dtype=np.uint8,
            all_touched=True
        )

        # Combine node and edge rasters
        combined_raster = np.maximum(node_rasterized, edge_rasterized)  # Combine both rasters by taking the maximum

        return {
            "data": combined_raster,
            "transform": reference_raster['transform'],
            "crs": ref_crs,
            "shape": reference_raster['shape']
        }