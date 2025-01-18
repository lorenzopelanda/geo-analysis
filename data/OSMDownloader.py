import osmnx as ox
import geopandas as gpd
from shapely.geometry import box

class OSMDownloader:
    def get_vector_area(self, bounding_box, tags):
        aoi_box = bounding_box.to_geometry()

        min_x, min_y, max_x, max_y = bounding_box.min_x, bounding_box.min_y, bounding_box.max_x, bounding_box.max_y
        gdf = ox.geometries_from_bbox(max_y, min_y, max_x, min_x, tags=tags)

        # Clip the geometries to the AOI
        osm_area = gpd.clip(gdf, aoi_box)

        return osm_area


