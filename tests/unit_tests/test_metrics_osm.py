import pytest
from unittest.mock import patch, MagicMock, PropertyMock
import numpy as np
import json
from greento.metrics.osm import osm


@pytest.fixture
def mock_osm_data():
    """Fixture per creare dati mock per osm."""
    return {
        'data': np.array([[0, 1, 1], [1, 0, 1]]),
        'transform': MagicMock(),
        'crs': 'EPSG:4326',
        'shape': (2, 3)
    }


@pytest.fixture
def mock_ghs_pop_data():
    """Fixture per creare dati GHS-POP mock."""
    return {
        'data': np.array([[10, 20, 30], [40, 50, 60]]),
        'transform': MagicMock(),
        'crs': 'EPSG:4326',
        'shape': (2, 3)
    }


@pytest.fixture
def mock_vector_traffic_area():
    """Fixture per creare dati vettoriali mock."""
    nodes = MagicMock()
    edges = MagicMock()
    return nodes, edges


@pytest.fixture
def metrics(mock_osm_data, mock_vector_traffic_area, mock_ghs_pop_data):
    """Fixture per creare un'istanza di osm."""
    return osm(mock_osm_data, mock_vector_traffic_area, mock_ghs_pop_data)


@patch('greento.metrics.osm.tqdm')
def test_green_area_per_person(mock_tqdm, metrics):
    """Test del metodo green_area_per_person."""
    mock_progress = MagicMock()
    mock_tqdm.return_value.__enter__.return_value = mock_progress

    result = metrics.green_area_per_person()
    result_dict = json.loads(result)

    assert 'green_area_per_person' in result_dict
    assert pytest.approx(result_dict['green_area_per_person'], 0.0001) == 1.9048

    mock_tqdm.assert_called()


@patch('greento.metrics.osm.tqdm')
def test_green_area_per_person_zero_population(mock_tqdm, metrics):
    """Test del metodo green_area_per_person con popolazione zero."""
    mock_progress = MagicMock()
    mock_tqdm.return_value.__enter__.return_value = mock_progress

    metrics.ghs_pop_data = {
        'data': np.zeros((2, 3)),
        'transform': MagicMock(),
        'crs': 'EPSG:4326',
        'shape': (2, 3)
    }

    result = metrics.green_area_per_person()
    result_dict = json.loads(result)

    assert 'green_area_per_person' in result_dict
    assert result_dict['green_area_per_person'] == float('inf')


@patch('greento.metrics.osm.tqdm')
@patch('greento.metrics.osm.ox.graph_from_gdfs')
@patch('greento.metrics.osm.ox.distance.nearest_nodes')
def test_get_isochrone_green_basic(mock_nearest_nodes, mock_graph_from_gdfs, mock_tqdm, metrics):
    """Test del metodo get_isochrone_green con parametri validi."""
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

    transform_mock = MagicMock()
    metrics.osm_file['transform'] = transform_mock
    inverse_transform = MagicMock()
    transform_mock.__invert__.return_value = inverse_transform
    inverse_transform.__mul__.return_value = (1, 1)

    metrics.osm_file['data'] = np.array([[0, 1], [1, 0]])

    with patch.object(metrics, '_estimate_distance_from_time', return_value=250):
        result = metrics.get_isochrone_green(45.123, 9.456, 10, 'walk')
        result_dict = json.loads(result)

        assert 'transport_mode' in result_dict
        assert result_dict['transport_mode'] == 'walk'
        assert result_dict['max_time'] == 10


@patch('greento.metrics.osm.tqdm')
def test_get_isochrone_green_invalid_params(mock_tqdm, metrics):
    """Test del metodo get_isochrone_green con parametri non validi."""
    mock_progress = MagicMock()
    mock_tqdm.return_value.__enter__.return_value = mock_progress

    with pytest.raises(ValueError, match="Coordinates not valid"):
        metrics.get_isochrone_green("not_a_number", 9.456, 10, 'walk')

    with pytest.raises(ValueError, match="Max time not valid"):
        metrics.get_isochrone_green(45.123, 9.456, -5, 'walk')

    with pytest.raises(ValueError, match="Transport mode not valid"):
        metrics.get_isochrone_green(45.123, 9.456, 10, 'teleport')


def test_estimate_distance_from_time(metrics):
    """Test del metodo _estimate_distance_from_time."""
    time_seconds = 600

    expected_walk = (5 / 3.6) * 600 / 1.15
    result_walk = metrics._estimate_distance_from_time(time_seconds, 'walk')
    assert pytest.approx(result_walk, 1) == expected_walk

    expected_bike = (15 / 3.6) * 600 / 1.2
    result_bike = metrics._estimate_distance_from_time(time_seconds, 'bike')
    assert pytest.approx(result_bike, 1) == expected_bike

    mock_speed = 5 / 3.6
    expected_unsupported = time_seconds * mock_speed
    result_unsupported = metrics._estimate_distance_from_time(time_seconds, 'unknown_mode')
    assert pytest.approx(result_unsupported, 1) == expected_unsupported