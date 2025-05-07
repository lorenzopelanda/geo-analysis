import pytest
import numpy as np
from greento.green.copernicus import copernicus

@pytest.fixture
def mock_copernicus():
    """Fixture per creare dati mock per copernicus."""
    return {
        "data": np.array([[10, 20, 30], [40, 50, 60], [10, 30, 40]]),
        "transform": "mock_transform",
        "crs": "EPSG:4326",
        "shape": (3, 3)
    }

@pytest.fixture
def green_copernicus(mock_copernicus):
    """Fixture per creare un'istanza di copernicus."""
    return copernicus(mock_copernicus)

def test_get_green_default(green_copernicus):
    """Test get_green con aree verdi predefinite."""
    result = green_copernicus.get_green()
    expected_data = np.array([[1, 1, 1], [0, 0, 0], [1, 1, 0]])

    np.testing.assert_array_equal(result["data"], expected_data)
    assert result["transform"] == "mock_transform"
    assert result["crs"] == "EPSG:4326"
    assert result["shape"] == (3, 3)

def test_get_green_custom_areas(green_copernicus):
    """Test get_green con aree verdi personalizzate."""
    custom_green_areas = frozenset([40, 50])
    result = green_copernicus.get_green(green_areas=custom_green_areas)
    expected_data = np.array([[0, 0, 0], [1, 1, 0], [0, 0, 1]])

    np.testing.assert_array_equal(result["data"], expected_data)
    assert result["transform"] == "mock_transform"
    assert result["crs"] == "EPSG:4326"
    assert result["shape"] == (3, 3)

def test_get_green_empty_data():
    """Test get_green con un dataset vuoto."""
    empty_copernicus = {
        "data": np.array([]),
        "transform": "mock_transform",
        "crs": "EPSG:4326",
        "shape": (0, 0)
    }
    green_copernicus = copernicus(empty_copernicus)
    result = green_copernicus.get_green()

    np.testing.assert_array_equal(result["data"], np.array([]))
    assert result["transform"] == "mock_transform"
    assert result["crs"] == "EPSG:4326"
    assert result["shape"] == (0, 0)