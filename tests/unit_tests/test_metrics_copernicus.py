import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import numpy as np
import json
import osmnx as ox
from greento.utils.geo import geo
from greento.metrics.copernicus import copernicus

class test_metrics_copernicus(unittest.TestCase):
    
    def setUp(self):
        self.mock_raster_data = {
            'data': np.array([[0, 1, 1], [1, 0, 1]]),
            'transform': MagicMock(),
            'crs': 'EPSG:4326',
            'shape': (2, 3)
        }
        
        self.mock_ghs_pop_data = {
            'data': np.array([[10, 20, 30], [40, 50, 60]]),
            'transform': MagicMock(),
            'crs': 'EPSG:4326',
            'shape': (2, 3)
        }
        
        nodes = MagicMock()
        edges = MagicMock()
        self.mock_vector_traffic_area = (nodes, edges)
        
        self.metrics = copernicus(self.mock_raster_data, self.mock_vector_traffic_area, self.mock_ghs_pop_data)

    @patch('greento.metrics.copernicus.tqdm')
    def test_green_area_per_person(self, mock_tqdm):
        mock_progress = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_progress
            
        result = self.metrics.green_area_per_person()
        result_dict = json.loads(result)
            
        self.assertIn('green_area_per_person', result_dict)
        self.assertAlmostEqual(result_dict['green_area_per_person'], 1.9048, places=4)
            
        mock_tqdm.assert_called()
    
    @patch('greento.metrics.copernicus.tqdm')
    def test_green_area_per_person_zero_population(self, mock_tqdm):
        mock_progress = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_progress
            
        self.metrics.ghs_pop_data = {
            'data': np.zeros((2, 3)),
            'transform': MagicMock(),
            'crs': 'EPSG:4326',
            'shape': (2, 3)
        }
            
        result = self.metrics.green_area_per_person()
        result_dict = json.loads(result)
            
        self.assertIn('green_area_per_person', result_dict)
        self.assertEqual(result_dict['green_area_per_person'], float('inf'))
    
    @patch('greento.metrics.copernicus.tqdm')
    @patch('greento.metrics.copernicus.ox.graph_from_gdfs')
    @patch('greento.metrics.copernicus.ox.distance.nearest_nodes')
    def test_get_isochrone_green_basic(self, mock_nearest_nodes, mock_graph_from_gdfs, mock_tqdm):
        mock_progress = MagicMock()
        type(mock_progress).n = PropertyMock(return_value=50)
        mock_tqdm.return_value.__enter__.return_value = mock_progress

        mock_G = MagicMock()
        mock_graph_from_gdfs.return_value = mock_G

        mock_nearest_nodes.return_value = (123, 100)

        mock_G.nodes = {
            123: {'y': 45.123, 'x': 9.456},
            456: {'y': 45.124, 'x': 9.457}
        }

        mock_G.neighbors.return_value = [456]

        mock_G.get_edge_data.return_value = {0: {'travel_time': 30}}

        edges_with_data = [(123, 456, {'length': 100, 'travel_time': 30})]
        mock_G.edges = MagicMock(return_value=edges_with_data)

        mock_G.edges.side_effect = lambda data=False: edges_with_data if data else [(123, 456)]

        transform_mock = MagicMock()
        self.metrics.copernicus_green['transform'] = transform_mock
        inverse_transform = MagicMock()
        transform_mock.__invert__.return_value = inverse_transform
        inverse_transform.__mul__.return_value = (1, 1)

        self.metrics.copernicus_green['data'] = np.array([[0, 1], [1, 0]])

        with patch.object(self.metrics, '_estimate_distance_from_time', return_value=250):
            def mock_n_gt(other):
                if other == 75:
                    return False
                elif other == 100:
                    return False
                return NotImplemented

            mock_progress.__gt__ = mock_n_gt

        try:
            result = self.metrics.get_isochrone_green(45.123, 9.456, 10, 'walk')
            result_dict = json.loads(result)

            self.assertIn('transport_mode', result_dict)
            self.assertEqual(result_dict['transport_mode'], 'walk')
            self.assertEqual(result_dict['max_time'], 10)
        except Exception as e:
            self.fail(f"Test not possible: {str(e)}")

    @patch('greento.metrics.copernicus.tqdm')
    def test_get_isochrone_green_invalid_params(self, mock_tqdm):
        mock_progress = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_progress
            
        with self.assertRaises(ValueError) as context:
            self.metrics.get_isochrone_green("not_a_number", 9.456, 10, 'walk')
        self.assertIn("Coordinates not valid", str(context.exception))
            
        with self.assertRaises(ValueError) as context:
            self.metrics.get_isochrone_green(45.123, 9.456, -5, 'walk')
        self.assertIn("Max time not valid", str(context.exception))
            
        with self.assertRaises(ValueError) as context:
            self.metrics.get_isochrone_green(45.123, 9.456, 10, 'teleport')
        self.assertIn("Transport mode not valid", str(context.exception))
    
    def test_estimate_distance_from_time(self):
        time_seconds = 600  
        expected_walk = (5/3.6) * 600 / 1.15  
        result_walk = self.metrics._estimate_distance_from_time(time_seconds, 'walk')
        self.assertAlmostEqual(result_walk, expected_walk, delta=1)
        
        expected_bike = (15/3.6) * 600 / 1.2 
        result_bike = self.metrics._estimate_distance_from_time(time_seconds, 'bike')
        self.assertAlmostEqual(result_bike, expected_bike, delta=1)
        
        mock_speed = 5 / 3.6  
        expected_unsupported = time_seconds * mock_speed  
        result_unsupported = self.metrics._estimate_distance_from_time(time_seconds, 'unknown_mode')
        self.assertAlmostEqual(result_unsupported, expected_unsupported, delta=1)

if __name__ == '__main__':
    unittest.main()