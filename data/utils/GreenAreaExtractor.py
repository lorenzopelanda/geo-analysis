import numpy as np
import json
from data.utils.UtilsInterface import GreenInterface
from data.downloader.OSMDownloader import OSMDownloader
from data.downloader.CopernicusDownloader import CopernicusDownloader

class GreenAreaExtractor(GreenInterface):
    def __init__(self, osm, copernicus):
        self.osm = osm
        self.copernicus = copernicus

    def get_green_area(self, **kwargs):
        if isinstance(self.osm, OSMDownloader):
            return self._get_osm_green_area(**kwargs)
        elif isinstance(self.copernicus, CopernicusDownloader):
            return self._get_copernicus_green_area(**kwargs)
        else:
            raise ValueError("Invalid data source specified.")

    def _get_osm_green_area(self,**kwargs):
        nodes, edges = self.osm
        green_tags = {
            'natural': ['fell', 'natural', 'grassland', 'heath', 'scrub', 'tree', 'wood',
                        'shrubbery', 'tree_row', 'tundra']
        }
        try:
            if kwargs:
                green_tags = kwargs

            green_nodes = nodes[nodes['natural'].isin(green_tags.get('natural', []))]
            green_edges = edges[edges['natural'].isin(green_tags.get('natural', []))]

            if green_nodes.empty or green_edges.empty:
                print("No green areas found in the bounding box")
                return None

            return (green_nodes, green_edges)
        except Exception as e:
            print(f"Error processing OSM green areas: {str(e)}")
            raise

    def _get_copernicus_green_area(self, **kwargs):
        if kwargs is None:
            green_areas = frozenset([10, 20, 30, 60, 95, 100])
        else:
            green_areas = kwargs.get('green_areas', frozenset([10, 20, 30, 60, 95, 100]))

        data = self.copernicus['data']
        transform = self.copernicus['transform']
        copernicus_crs = self.copernicus['crs']
        copernicus_shape = self.copernicus['shape']

        green_mask = np.isin(data, list(green_areas))
        raster = np.zeros_like(data, dtype=np.uint8)
        raster[green_mask] = 1
        return{
            "data": raster,
            "transform": transform,
            "crs": copernicus_crs,
            "shape": copernicus_shape
        }

