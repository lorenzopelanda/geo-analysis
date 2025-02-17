import osmnx as ox
import rasterio
import geopandas as gpd
import numpy as np
import pandas as pd
from rasterio.features import rasterize
from shapely.geometry import box
from concurrent.futures import ThreadPoolExecutor, as_completed

ox.settings.overpass_settings = "[out:json][timeout:60][maxsize:10485760];"

class OSMDownloader:

    def get_vector_area(self, bounding_box, tags):
        aoi_box = bounding_box.to_geometry()

        bbox = (bounding_box.min_x,  # left
                             bounding_box.min_y,  # bottom
                             bounding_box.max_x,  # right
                             bounding_box.max_y)  # top
        if isinstance(tags, str):
            tags = {tags: True}
        gdf = ox.features_from_bbox(bbox=bbox, tags=tags)
        # Clip the geometries to the AOI
        osm_area = gpd.clip(gdf, aoi_box)

        return osm_area

    # def get_vector_area(self, bounding_box, tags):
    #     """
    #     Download the OSM vector data for a given bounding box and tags.
    #     """
    #     aoi_box = bounding_box.to_geometry()
    #
    #     # Reorder coordinates to match (left, bottom, right, top)
    #     bbox = (bounding_box.min_x,  # left
    #             bounding_box.min_y,  # bottom
    #             bounding_box.max_x,  # right
    #             bounding_box.max_y)  # top
    #     print(f"Bounding box coordinates: {bbox}")
    #     gdf = ox.features_from_bbox(bbox=bbox, tags={tags: True})
    #
    #     # Clip the geometries to the AOI
    #     osm_area = gpd.clip(gdf, aoi_box)
    #
    #     return osm_area

    def get_traffic_area(self, bounding_box, network_type, reference_raster):
        """
        Download the OSM network data for a given bounding box and network type, and rasterize it to a reference raster.
        """
        aoi_box = bounding_box.to_geometry()

        min_x, min_y, max_x, max_y = bounding_box.min_x, bounding_box.min_y, bounding_box.max_x, bounding_box.max_y
        bbox = (bounding_box.min_x,  # left
                bounding_box.min_y,  # bottom
                bounding_box.max_x,  # right
                bounding_box.max_y)
        print(f"Bounding box coordinates: {bbox}")
        # Download the OSM network data
        if network_type in ["bus", "tram", "train", "subway"]:
            tags = {"route": ["bus", "tram", "train", "subway"]}
            gdf = ox.features_from_bbox(bbox=bbox, tags=tags)
        else:
            graph = ox.graph_from_bbox(bbox=bbox, network_type=network_type, simplify=True)

        # Convert the graph to Geodataframe
        if network_type in ["bus", "tram", "train", "subway"]:
            osm_area = gpd.clip(gdf, aoi_box)
        else:
            edges = ox.graph_to_gdfs(graph, nodes=False, edges=True)

            # Clip the geometries to the AOI
            osm_area = gpd.clip(edges, aoi_box)

        # Create an empty raster with the same shape as the reference raster
        ref_data, ref_transform, ref_crs, ref_shape = reference_raster
        rasterized = np.zeros(ref_shape, dtype=np.uint8)

        # Rasterize the vector data
        shapes = [(geom, 1) for geom in osm_area.geometry if geom is not None]
        rasterized = rasterize(
            shapes=shapes,
            out_shape=ref_shape,
            transform=ref_transform,
            fill=0,
            dtype=np.uint8,
            all_touched=True
        )

        return osm_area, {
            "data": rasterized,
            "transform": ref_transform,
            "crs": ref_crs,
            "shape": ref_shape
        }