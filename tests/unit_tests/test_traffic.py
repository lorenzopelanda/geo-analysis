import pytest
from unittest.mock import patch, MagicMock
import geopandas as gpd
from shapely.geometry import Point, LineString
from greento.traffic.traffic import traffic
from greento.boundingbox import boundingbox


@pytest.fixture
def bounding_box():
    """Fixture per creare un bounding box."""
    return boundingbox(min_x=0, min_y=0, max_x=1, max_y=1)


@pytest.fixture
def traffic_instance(bounding_box):
    """Fixture per creare un'istanza di traffic."""
    return traffic(bounding_box)


@patch("greento.traffic.traffic.ox.graph_from_polygon")
@patch("greento.traffic.traffic.ox.graph_to_gdfs")
@patch("greento.traffic.traffic.gpd.clip")
def test_get_traffic_area_success(mock_clip, mock_graph_to_gdfs, mock_graph_from_polygon, traffic_instance):
    """Test get_traffic_area con dati validi."""
    mock_graph = MagicMock()
    mock_graph_from_polygon.return_value = mock_graph

    mock_nodes = gpd.GeoDataFrame({
        'geometry': [Point(0, 0), Point(1, 1)],
        'attribute': ['node1', 'node2']
    }, crs="EPSG:4326")

    mock_edges = gpd.GeoDataFrame({
        'geometry': [LineString([(0, 0), (1, 1)])],
        'attribute': ['edge1']
    }, crs="EPSG:4326")

    mock_graph_to_gdfs.return_value = (mock_nodes, mock_edges)
    mock_clip.side_effect = lambda gdf, bbox: gdf

    result_nodes, result_edges = traffic_instance.get_traffic_area(network_type="drive")

    assert not result_nodes.empty
    assert not result_edges.empty
    assert len(result_nodes) == 2
    assert len(result_edges) == 1
    mock_graph_from_polygon.assert_called_once()
    mock_graph_to_gdfs.assert_called_once()
    mock_clip.assert_called()


@patch("greento.traffic.traffic.ox.graph_from_polygon")
def test_get_traffic_area_no_graph(mock_graph_from_polygon, traffic_instance):
    """Test get_traffic_area quando la creazione del grafo fallisce."""
    mock_graph_from_polygon.return_value = None

    result = traffic_instance.get_traffic_area(network_type="drive")

    assert result is None
    mock_graph_from_polygon.assert_called_once()


@patch("greento.traffic.traffic.ox.graph_from_polygon")
@patch("greento.traffic.traffic.ox.graph_to_gdfs")
def test_get_traffic_area_empty_data(mock_graph_to_gdfs, mock_graph_from_polygon, traffic_instance):
    """Test get_traffic_area quando nodi o archi sono vuoti."""
    mock_graph = MagicMock()
    mock_graph_from_polygon.return_value = mock_graph

    mock_nodes = gpd.GeoDataFrame(columns=['geometry'], crs="EPSG:4326")
    mock_edges = gpd.GeoDataFrame(columns=['geometry'], crs="EPSG:4326")

    mock_graph_to_gdfs.return_value = (mock_nodes, mock_edges)
    result = traffic_instance.get_traffic_area(network_type="drive")

    assert result is None
    mock_graph_from_polygon.assert_called_once()
    mock_graph_to_gdfs.assert_called_once()


@patch("greento.traffic.traffic.ox.graph_from_polygon")
def test_get_traffic_area_invalid_network_type(mock_graph_from_polygon, traffic_instance):
    """Test get_traffic_area con un tipo di rete non valido."""
    mock_graph_from_polygon.side_effect = ValueError("Invalid network type")

    with pytest.raises(ValueError, match="Invalid network type"):
        traffic_instance.get_traffic_area(network_type="invalid_type")

    mock_graph_from_polygon.assert_called_once()