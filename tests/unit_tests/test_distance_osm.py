import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import numpy as np
import networkx as nx
import geopandas as gpd
from shapely.geometry import Point, LineString
import json
import rasterio
from greento.distance.osm import osm
from greento.utils.geo import geo

class test_distance_osm(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_transform = rasterio.Affine(0.1, 0, 10, 0, -0.1, 50)
        self.mock_osm_green = {
            'data': np.zeros((10, 10), dtype=np.int8),
            'transform': self.mock_transform,
            'crs': 'EPSG:4326',
            'shape': (10, 10)
        }
        
        self.mock_osm_green['data'][3:6, 3:6] = 1
        
        nodes = gpd.GeoDataFrame(
            {
                'osmid': [1, 2, 3, 4, 5],
                'x': [10.1, 10.2, 10.3, 10.4, 10.5],
                'y': [50.1, 50.2, 50.3, 50.4, 50.5],
                'geometry': [
                    Point(10.1, 50.1),
                    Point(10.2, 50.2),
                    Point(10.3, 50.3),
                    Point(10.4, 50.4),
                    Point(10.5, 50.5)
                ]
            }
        )
        
        edges = gpd.GeoDataFrame(
            {
                'u': [1, 2, 3, 4],
                'v': [2, 3, 4, 5],
                'length': [100, 200, 150, 300],
                'highway': ['residential', 'residential', 'primary', 'primary'],
                'geometry': [
                    LineString([(10.1, 50.1), (10.2, 50.2)]),
                    LineString([(10.2, 50.2), (10.3, 50.3)]),
                    LineString([(10.3, 50.3), (10.4, 50.4)]),
                    LineString([(10.4, 50.4), (10.5, 50.5)])
                ]
            }
        )
        
        self.mock_vector_traffic_area = (nodes, edges)
        
        self.distance_osm = osm(
            self.mock_osm_green, 
            self.mock_vector_traffic_area
        )

    @patch('greento.distance.osm.ox')
    @patch('greento.distance.osm.geo')
    @patch('greento.distance.osm.cKDTree')
    @patch('greento.distance.osm.nx')
    @patch('greento.distance.osm.tqdm')
    def test_get_nearest_green_position(self, mock_tqdm, mock_nx, mock_cKDTree, mock_geo, mock_ox):
        """Test the get_nearest_green_position method."""
        mock_progress = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_progress
        
        mock_graph = MagicMock()
        mock_ox.graph_from_gdfs.return_value = mock_graph
        
        mock_ox.distance.nearest_nodes.return_value = 1
        
        mock_geo_utils_instance = MagicMock()
        mock_geo_utils_instance.haversine_distance.return_value = 1.5
        mock_geo.return_value = mock_geo_utils_instance
        
        with patch('rasterio.transform.xy', return_value=([10.35, 10.45], [49.65, 49.55])):
            
            with patch.object(self.distance_osm, 'get_nearest_green_position', 
                              return_value=(50.3, 10.3)):
                
                lat, lon = 50.2, 10.2
                result = self.distance_osm.get_nearest_green_position(lat, lon)
                
                self.assertEqual(result, (50.3, 10.3))
        
    @patch('greento.distance.osm.ox')
    @patch('greento.distance.osm.tqdm')
    def test_directions(self, mock_tqdm, mock_ox):
        """Test the directions method."""
        mock_progress = MagicMock()
        type(mock_progress).n = PropertyMock(return_value=0)  
        mock_tqdm.return_value.__enter__.return_value = mock_progress
        
        mock_graph = MagicMock()
        
        mock_edges = {}
        for u, v in [(1, 2), (2, 3), (3, 4), (4, 5)]:
            if u not in mock_edges:
                mock_edges[u] = {}
            mock_edges[u][v] = {0: {'length': 100*v, 'travel_time': 10*v}}
        
        mock_graph.__getitem__.side_effect = lambda u: mock_edges.get(u, {})
        
        mock_ox.graph_from_gdfs.return_value = mock_graph
        mock_ox.routing.add_edge_speeds.return_value = mock_graph
        mock_ox.routing.add_edge_travel_times.return_value = mock_graph
        mock_ox.distance.nearest_nodes.side_effect = [1, 5]  
        mock_ox.shortest_path.return_value = [1, 2, 3, 4, 5]  
        
        with patch.object(self.distance_osm, 'directions', 
                          return_value=json.dumps({"distance_km": 1.2, "estimated_time_minutes": 30})):
            
            lat1, lon1 = 50.1, 10.1  
            lat2, lon2 = 50.5, 10.5  
            transport_mode = "walk"
            
            self.distance_osm.preprocessed_graph = None
            result = self.distance_osm.directions(lat1, lon1, lat2, lon2, transport_mode)
            
            result_dict = json.loads(result)
            
            self.assertIn("distance_km", result_dict)
            self.assertIn("estimated_time_minutes", result_dict)
            self.assertEqual(result_dict["estimated_time_minutes"], 30)
            self.assertEqual(result_dict["distance_km"], 1.2)

if __name__ == '__main__':
    unittest.main()