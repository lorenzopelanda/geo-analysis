import pytest
from unittest.mock import patch, MagicMock, mock_open
from greento.data.ghspop import ghspop
from greento.data.ghspop_io import ghspop_io
from greento.boundingbox import boundingbox
from shapely.geometry import box
import numpy as np
import numpy.testing as npt


@pytest.fixture
def mock_downloader():
    """Fixture to create a mock ghspop instance."""
    return ghspop(shapefile="mock_shapefile.shp")


@patch("greento.data.ghspop.gpd.read_file")
def test_load_shapefile(mock_read_file, mock_downloader):
    mock_gdf = MagicMock()
    mock_gdf.crs = "EPSG:4326"
    mock_read_file.return_value = mock_gdf

    result = mock_downloader._ghspop__load_shapefile()

    assert result == mock_gdf
    mock_read_file.assert_called_once_with("mock_shapefile.shp")


@patch("greento.data.ghspop_io.requests.get")
def test_download_tile_failure(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    io_handler = ghspop_io()
    result = io_handler._download_tile("mock_tile_id")

    assert result is None
    mock_get.assert_called_once()


@patch("os.path.exists")
@patch("os.remove")
@patch("greento.data.ghspop_io.zipfile.ZipFile")
def test_extract_tif_file(mock_zipfile, mock_remove, mock_exists):
    mock_zip = MagicMock()
    mock_zipfile.return_value.__enter__.return_value = mock_zip
    mock_zip.namelist.return_value = ["mock_file.tif"]

    mock_exists.return_value = True

    io_handler = ghspop_io()
    with patch("builtins.open", mock_open()):
        result = io_handler._extract_tif_file("mock_zip_path")

    assert result == "extracted_files/mock_file.tif"
    mock_zipfile.assert_called_once_with("mock_zip_path", "r")
    mock_zip.extract.assert_called_once_with("mock_file.tif", "extracted_files")


@patch("greento.data.ghspop.box")
@patch("greento.data.ghspop.gpd.GeoDataFrame")
def test_get_tiles_for_bounds(mock_gdf, mock_box, mock_downloader):
    bounds = boundingbox(min_x=0, min_y=0, max_x=1, max_y=1)

    mock_bbox = MagicMock()
    mock_box.return_value = mock_bbox

    mock_bbox_gdf = MagicMock()
    mock_gdf.return_value = mock_bbox_gdf
    mock_bbox_gdf.geometry = [mock_bbox]

    mock_tiles_gdf = MagicMock()
    mock_tiles_gdf.intersects.return_value = [True, False]

    filtered_gdf = MagicMock()
    mock_tiles_gdf.__getitem__.return_value = filtered_gdf

    filtered_gdf.iterrows.return_value = [
        (0, {"tile_id": "tile_1"})  
    ]

    result = mock_downloader._ghspop__get_tiles_for_bounds(bounds, mock_tiles_gdf)

    assert result == ["tile_1"]

@patch("rasterio.open")
@patch("os.path.exists")
@patch("greento.data.ghspop_io.ghspop_io._download_tile")  
@patch("greento.data.ghspop_io.ghspop_io._extract_tif_file")  
def test_process_single_tile(mock_extract_tif, mock_download_tile, mock_exists, mock_rasterio_open):
    downloader = ghspop(shapefile="mock_shapefile.shp")
    
    # Configura i mock
    mock_download_tile.return_value = "mock_zip_path"
    mock_extract_tif.return_value = "mock_tif_path"
    mock_exists.return_value = True

    mock_dataset = MagicMock()
    mock_dataset.read.return_value = np.array([[1, 2], [3, 4]])
    mock_dataset.transform = "mock_transform"
    mock_dataset.crs = "mock_crs"
    mock_dataset.shape = (2, 2)
    mock_rasterio_open.return_value.__enter__.return_value = mock_dataset

    result = downloader._process_single_tile("mock_tile_id")

    assert result is not None
    npt.assert_array_equal(result[0], np.array([[1, 2], [3, 4]]))
    assert result[1] == "mock_transform"
    assert result[2] == "mock_crs"
    assert result[3] == (2, 2)

    mock_download_tile.assert_called_once_with("mock_tile_id")
    mock_extract_tif.assert_called_once_with("mock_zip_path")
    mock_rasterio_open.assert_called_once_with("mock_tif_path")