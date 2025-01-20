import geopandas as gpd
from shutil import rmtree
from shapely.geometry import Point
import requests
import zipfile
import os
import osmnx as ox
import numpy as np
import rasterio
from data.CopernicusDownloader import CopernicusDownloader


ox.settings.use_cache = False

class GHSPOPDownloader:
    def __init__(self, address, shapefile_path, extracted_dir="extracted_files"):
        self.address = address
        self.shapefile_path = shapefile_path
        self.extracted_dir = extracted_dir
        self.lat, self.lon = self.geocode_address()

    def geocode_address(self):
        location = ox.geocode(self.address)
        return location[1], location[0]

    def remove_existing_directory(self):
        if os.path.exists(self.extracted_dir):
            rmtree(self.extracted_dir)

    def load_shapefile(self):
        tiles_gdf = gpd.read_file(self.shapefile_path)
        if tiles_gdf.crs != "EPSG:4326":
            tiles_gdf = tiles_gdf.to_crs("EPSG:4326")
        print(f"Tiles CRS: {tiles_gdf.crs}")
        return tiles_gdf

    def create_point_gdf(self):
        point = Point(self.lat, self.lon)
        return gpd.GeoDataFrame([{'geometry': point}], crs="EPSG:4326")

    def get_tile_id(self, tiles_gdf, point_gdf):
        current_tile = tiles_gdf[tiles_gdf.contains(point_gdf.geometry.iloc[0])]
        if not current_tile.empty:
            return current_tile.iloc[0]['tile_id']
        return None

    def download_tile(self, tile_id):
        url = f"https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_POP_GLOBE_R2023A/GHS_POP_E2030_GLOBE_R2023A_4326_30ss/V1-0/tiles/GHS_POP_E2030_GLOBE_R2023A_4326_30ss_V1_0_{tile_id}.zip"
        response = requests.get(url)
        if response.status_code == 200:
            zip_path = 'tile_download.zip'
            with open(zip_path, 'wb') as file:
                file.write(response.content)
            return zip_path
        return None

    # def extract_tif_file(self, zip_path):
    #     tif_path = None
    #     with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    #         for file in zip_ref.namelist():
    #             if file.endswith('.tif'):
    #                 zip_ref.extract(file, self.extracted_dir)
    #                 tif_path = os.path.join(self.extracted_dir, file)
    #                 print(f"Extracted TIF file to: {tif_path}")
    #                 if not os.path.exists(tif_path):
    #                     print(f"TIF file does not exist at {tif_path}")
    #                     tif_path = None
    #     os.remove(zip_path)
    #     self.remove_existing_directory()
    #     return tif_path

    def extract_tif_file(self, zip_path):
        """
        Extract TIF file from zip archive.
        Files will be kept until explicitly cleaned up later.
        """
        tif_path = None
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for file in zip_ref.namelist():
                    if file.endswith('.tif'):
                        zip_ref.extract(file, self.extracted_dir)
                        tif_path = os.path.join(self.extracted_dir, file)
                        print(f"Extracted TIF file to: {tif_path}")
                        if not os.path.exists(tif_path):
                            print(f"TIF file does not exist at {tif_path}")
                            tif_path = None
                        break  # Extract only the first TIF file found

            # Remove only the zip file after successful extraction
            if os.path.exists(zip_path):
                os.remove(zip_path)

            return tif_path

        except Exception as e:
            print(f"Error during TIF extraction: {str(e)}")
            return None

    def get_population_area(self):
        self.remove_existing_directory()
        tiles_gdf = self.load_shapefile()
        point_gdf = self.create_point_gdf()
        tile_id = self.get_tile_id(tiles_gdf, point_gdf)
        if tile_id:
            print(f"Tile ID: {tile_id}")
            zip_path = self.download_tile(tile_id)
            if zip_path:
                data = self.extract_tif_file(zip_path)
                if data is not None:
                    with rasterio.open(os.path.join(self.extracted_dir, zip_path.replace('.zip', '.tif'))) as dataset:
                        transform = dataset.transform
                        crs = dataset.crs
                        shape = dataset.shape
                    return data, transform, crs, shape
        return None, None, None, None




# Example usage
