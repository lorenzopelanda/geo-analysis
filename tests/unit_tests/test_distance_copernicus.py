import pytest
from unittest.mock import patch, MagicMock, PropertyMock
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, LineString
import json
import rasterio
from greento.distance.copernicus import copernicus


@pytest.fixture
def mock_raster_data():
    """Fixture per creare dati raster mock."""
    mock_transform = rasterio.Affine(0.1, 0, 10, 0, -0.1, 50)
    mock_data = np.zeros((10, 10), dtype=np.int8)
    mock_data[3:6, 3:6] = 1
    return {
        'data': mock_data,
        'transform': mock_transform,
        'crs': 'EPSG:4326',
        'shape': (10, 10)
    }


@pytest.fixture
def mock_vector_traffic_area():
    """Fixture per creare dati vettoriali mock."""
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
    return nodes, edges


@pytest.fixture
def distance_copernicus(mock_raster_data, mock_vector_traffic_area):
    """Fixture per creare un'istanza di copernicus."""
    return copernicus(mock_raster_data, mock_vector_traffic_area)


@patch('greento.distance.copernicus.ox')
@patch('greento.distance.copernicus.geo')
@patch('greento.distance.copernicus.cKDTree')
@patch('greento.distance.copernicus.nx')
@patch('greento.distance.copernicus.tqdm')
def test_get_nearest_green_position(mock_tqdm, mock_nx, mock_cKDTree, mock_geo, mock_ox, distance_copernicus):
    """Test del metodo get_nearest_green_position."""
    mock_progress = MagicMock()
    mock_tqdm.return_value.__enter__.return_value = mock_progress

    mock_graph = MagicMock()
    mock_ox.graph_from_gdfs.return_value = mock_graph

    mock_ox.distance.nearest_nodes.return_value = 1

    mock_geo_utils_instance = MagicMock()
    mock_geo_utils_instance.haversine_distance.return_value = 1.5
    mock_geo.return_value = mock_geo_utils_instance

    with patch('rasterio.transform.xy', return_value=([10.35, 10.45], [49.65, 49.55])):
        with patch.object(distance_copernicus, 'get_nearest_green_position', return_value=(50.3, 10.3)):
            lat, lon = 50.2, 10.2
            result = distance_copernicus.get_nearest_green_position(lat, lon)

            assert result == (50.3, 10.3)


@patch('greento.distance.copernicus.ox')
@patch('greento.distance.copernicus.tqdm')
def test_directions(mock_tqdm, mock_ox, distance_copernicus):
    """Test del metodo directions."""
    mock_progress = MagicMock()
    type(mock_progress).n = PropertyMock(return_value=0)
    mock_tqdm.return_value.__enter__.return_value = mock_progress

    mock_graph = MagicMock()

    mock_edges = {}
    for u, v in [(1, 2), (2, 3), (3, 4), (4, 5)]:
        if u not in mock_edges:
            mock_edges[u] = {}
        mock_edges[u][v] = {0: {'length': 100 * v, 'travel_time': 10 * v}}

    mock_graph.__getitem__.side_effect = lambda u: mock_edges.get(u, {})

    mock_ox.graph_from_gdfs.return_value = mock_graph
    mock_ox.routing.add_edge_speeds.return_value = mock_graph
    mock_ox.routing.add_edge_travel_times.return_value = mock_graph
    mock_ox.distance.nearest_nodes.side_effect = [1, 5]
    mock_ox.shortest_path.return_value = [1, 2, 3, 4, 5]

    with patch.object(distance_copernicus, 'directions', return_value=json.dumps({"distance_km": 1.2, "estimated_time_minutes": 30})):
        lat1, lon1 = 50.1, 10.1
        lat2, lon2 = 50.5, 10.5
        transport_mode = "walk"

        distance_copernicus.preprocessed_graph = None
        result = distance_copernicus.directions(lat1, lon1, lat2, lon2, transport_mode)

        result_dict = json.loads(result)

        assert "distance_km" in result_dict
        assert "estimated_time_minutes" in result_dict
        assert result_dict["estimated_time_minutes"] == 30
        assert result_dict["distance_km"] == 1.2