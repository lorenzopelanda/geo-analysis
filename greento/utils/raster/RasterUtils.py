import json
import numpy as np
import rasterio
import rasterio.transform
import time
from tqdm import tqdm
from rasterio.warp import calculate_default_transform, reproject, Resampling
from greento.utils.UtilsInterface import UtilsInterface

class RasterUtils(UtilsInterface):
    """
    A class to provide utility functions for processing raster data.

    Attributes:
    ----------
    copernicus : dict
        The Copernicus data containing 'data', 'transform', 'crs', and 'shape'.

    Methods:
    -------
    filter_copernicus_with_osm(copernicus_green):
        Filters the Copernicus data using OSM green data.
    get_land_use_percentages():
        Calculates the land use percentages from the Copernicus data.
    raster_to_crs(dst_crs):
        Transforms a raster to a new CRS with a different resolution and extent.
    """
    def __init__(self, copernicus):
        """
        Initializes the RasterUtils with Copernicus data.

        Parameters:
        ----------
        copernicus : dict
            The Copernicus data containing 'data', 'transform', 'crs', and 'shape'.
        """
        self.copernicus = copernicus

    def filter_copernicus_with_osm(self, copernicus_green):
        """
        Filters the Copernicus data using OSM green data.

        Parameters:
        ----------
        copernicus_green : dict
            The Copernicus green area data containing 'data', 'transform', 'crs', and 'shape'.

        Returns:
        -------
        dict
            The filtered raster data.
        
        Raises:
        ------
        ValueError
            If the raster shapes do not match.
        """
        copernicus_data = copernicus_green['data']
        osm_data = self.osm_green['data']

        if copernicus_data.shape != osm_data.shape:
            raise ValueError("Raster shapes do not match")

        filtered_data = np.where((osm_data == 1) & (copernicus_data == 1), 1, 0)

        filtered_raster = {
            'data': filtered_data,
            'transform': copernicus_green['transform'],
            'crs': copernicus_green['crs'],
            'shape':copernicus_green['shape']
        }

        return filtered_raster

    def get_land_use_percentages(self):
        """
        Calculates the land use percentages from the Copernicus data.

        Returns:
        -------
        str
            A JSON string containing the land use percentages.
        """
        start_time = time.time()

        data = self.copernicus['data']
        labels = {
            10: "Forest and trees",
            20: "Shrubs",
            30: "Grassland",
            40: "Cropland",
            50: "Buildings",
            60: "Sparse vegetation",
            70: "Snow and Ice",
            80: "Permanent water bodies",
            90: "Herbaceous wetland",
            95: "Mangroves",
            100: "Moss and lichen"
        }
        values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100]
        
        progress_bar = None
        elapsed_time = time.time() - start_time
        if elapsed_time > 5: 
            progress_bar = tqdm(total=100, desc="Processing Land Use Percentages", unit="%") 

        unique, counts = np.unique(data, return_counts=True)
        land_use_types = dict(zip(unique, counts))
        total = sum(land_use_types.values())

        percentages = {labels.get(land_use, land_use): round((count / total) * 100, 4) for land_use, count in
                    land_use_types.items() if land_use in values}
        if progress_bar:
            progress_bar.update(50)  

        if progress_bar:
            progress_bar.update(50) 

        return json.dumps(percentages)
    
    def raster_to_crs(self,dst_crs):
        """
        Transforms a raster to a new CRS with a different resolution and extent.

        Parameters:
        ----------
        dst_crs : str
            The destination coordinate reference system.

        Returns:
        -------
        dict
            The transformed raster data.
        
        Raises:
        ------
        ValueError
            If the shape of the data is incorrect.
        """
        src_data = self.copernicus['data']
        src_transform = self.copernicus['transform']
        src_crs = self.copernicus['crs']
        shape = self.copernicus['shape']

        if len(shape) == 2:
            height, width = shape
            count = 1
        elif len(shape) == 3:
            count, height, width = shape
        else:
            raise ValueError("Shape of the data incorrect!")

        bounds = rasterio.transform.array_bounds(height, width, src_transform)

        transform, width, height = calculate_default_transform(
            src_crs,
            dst_crs,
            width,
            height,
            *bounds
        )

        dst_data = np.empty((count, int(height), int(width)), dtype=src_data.dtype)

        with tqdm(total=100, desc="Reprojecting raster data") as pbar:
            for i in range(count):
                reproject(
                    source=src_data[i] if count > 1 else src_data,
                    destination=dst_data[i] if count > 1 else dst_data[0],
                    src_transform=src_transform,
                    src_crs=src_crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.nearest
                )
                pbar.update(1)
            return {
                'data': dst_data,
                'crs': dst_crs,
                'transform': transform
            }