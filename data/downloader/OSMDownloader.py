import osmnx as ox
import rasterio
import geopandas as gpd
import numpy as np
import pandas as pd
from rasterio.features import rasterize
from shapely.geometry import box
from concurrent.futures import ThreadPoolExecutor, as_completed

ox.settings.overpass_url = "https://overpass.kumi.systems/api/interpreter"

class OSMDownloader:

    def get_vector_area(self, bounding_box, tags):
        aoi_box = bounding_box.to_geometry()

        try:
            polygon = aoi_box
            gdf = ox.features_from_polygon(polygon, tags)

            if not gdf.empty:
                # Clip the geometries to the AOI
                osm_area = gpd.clip(gdf, aoi_box)
                return osm_area
            return gdf

        except Exception as e:
            print(f"Error downloading OSM data: {str(e)}")
            raise

    def get_traffic_area(self, bounding_box, network_type):
        """
        Download the OSM network data for a given bounding box and network type, and rasterize it to a reference raster.
        """
        aoi_box = bounding_box.to_geometry()

        # Download the OSM network data
        if network_type in ["bus", "tram", "train", "subway"]:
            tags = {"route": ["bus", "tram", "train", "subway"]}
            gdf = ox.features_from_polygon(aoi_box, tags=tags)
        else:
            graph = ox.graph_from_polygon(aoi_box, network_type, simplify=True)

        # Convert the graph to Geodataframe
        if network_type in ["bus", "tram", "train", "subway"]:
            osm_area = gpd.clip(gdf, aoi_box)
        else:
            edges = ox.graph_to_gdfs(graph, nodes=False, edges=True)

            # Clip the geometries to the AOI
            osm_area = gpd.clip(edges, aoi_box)

        return osm_area