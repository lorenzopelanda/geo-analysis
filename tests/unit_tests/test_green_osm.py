import pytest
import geopandas as gpd
from shapely.geometry import Point, LineString
from greento.green.osm import osm

@pytest.fixture
def mock_osm_data():
    """Fixture per creare dati mock per osm."""
    mock_nodes = gpd.GeoDataFrame({
        'id': [1, 2, 3],
        'natural': ['wood', 'tree', 'rock'],
        'geometry': [Point(0, 0), Point(1, 1), Point(2, 2)]
    }, crs="EPSG:4326")

    mock_edges = gpd.GeoDataFrame({
        'id': [1, 2],
        'landuse': ['forest', 'industrial'],
        'geometry': [LineString([(0, 0), (1, 1)]), LineString([(1, 1), (2, 2)])]
    }, crs="EPSG:4326")

    return mock_nodes, mock_edges

@pytest.fixture
def green_osm(mock_osm_data):
    """Fixture per creare un'istanza di osm."""
    return osm(mock_osm_data)

def test_get_green_default(green_osm):
    """Test get_green con tag verdi predefiniti."""
    result_nodes, result_edges = green_osm.get_green()

    expected_nodes = gpd.GeoDataFrame({
        'id': [1, 2],
        'natural': ['wood', 'tree'],
        'geometry': [Point(0, 0), Point(1, 1)]
    }, crs="EPSG:4326")

    expected_edges = gpd.GeoDataFrame({
        'id': [1],
        'landuse': ['forest'],
        'geometry': [LineString([(0, 0), (1, 1)])]
    }, crs="EPSG:4326")

    assert result_nodes.equals(expected_nodes)
    assert result_edges.equals(expected_edges)

def test_get_green_custom_tags(green_osm):
    """Test get_green con tag verdi personalizzati."""
    custom_tags = {
        'natural': ['rock'],
        'landuse': ['industrial']
    }
    result_nodes, result_edges = green_osm.get_green(green_tags=custom_tags)

    expected_nodes = gpd.GeoDataFrame({
        'id': [3],
        'natural': ['rock'],
        'geometry': [Point(2, 2)]
    }, crs="EPSG:4326")

    expected_edges = gpd.GeoDataFrame({
        'id': [2],
        'landuse': ['industrial'],
        'geometry': [LineString([(1, 1), (2, 2)])]
    }, crs="EPSG:4326")

    result_nodes = result_nodes.sort_values(by="id").reset_index(drop=True)
    expected_nodes = expected_nodes.sort_values(by="id").reset_index(drop=True)
    result_edges = result_edges.sort_values(by="id").reset_index(drop=True)
    expected_edges = expected_edges.sort_values(by="id").reset_index(drop=True)

    assert result_nodes.equals(expected_nodes)
    assert result_edges.equals(expected_edges)

def test_get_green_empty_data():
    """Test get_green con GeoDataFrame vuoti."""
    empty_osm = (gpd.GeoDataFrame(geometry=[]), gpd.GeoDataFrame(geometry=[]))
    green_osm = osm(empty_osm)
    result_nodes, result_edges = green_osm.get_green()

    assert result_nodes.empty
    assert result_edges.empty