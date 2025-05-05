import numpy as np
from tqdm import tqdm
from greento.green.interface import interface

class copernicus(interface):
    """
    A class to process green areas using Copernicus data.

    Attributes
    ----------
    copernicus : dict
        The Copernicus data containing 'data', 'transform', 'crs', and 'shape'.

    Methods
    -------
    get_green(**kwargs) -> dict
        Filters and processes green areas from the Copernicus data.
    """

    def __init__(self, copernicus: dict) -> None:
        """
        Initializes the GreenCopernicus class with Copernicus data.

        Parameters
        ----------
        copernicus : dict
            A dictionary containing the Copernicus data with the following keys:
                - 'data': The raster data.
                - 'transform': The affine transform of the raster.
                - 'crs': The coordinate reference system of the raster.
                - 'shape': The shape of the raster.

        Returns
        -------
        None
        """
        self.copernicus = copernicus

    def get_green(self, **kwargs) -> dict:
        """
        Filters and processes green areas from the Copernicus data.

        Parameters
        ----------
        **kwargs : dict, optional
            Additional arguments to specify green areas.
            - green_areas (frozenset, optional): A set of values representing green areas 
              (default is frozenset([10, 20, 30])).

        Returns
        -------
        dict
            A dictionary containing the filtered green areas with the following keys:
                - 'data': The binary raster data where green areas are marked as 1.
                - 'transform': The affine transform of the raster.
                - 'crs': The coordinate reference system of the raster.
                - 'shape': The shape of the raster.

        Notes
        -----
        The method uses the `numpy` library to filter raster data and the `tqdm` library to display progress.
        """
        if kwargs is None:
            green_areas = frozenset([10,20, 30]) # 10: tree cover, 20: shrubland, 30: grassland
        else:
            green_areas = kwargs.get('green_areas', frozenset([10, 20, 30]))

        data = self.copernicus['data']
        transform = self.copernicus['transform']
        copernicus_crs = self.copernicus['crs']
        copernicus_shape = self.copernicus['shape']

        with tqdm(total=100, desc="Filtering Copernicus green areas", leave=False) as pbar:
            green_mask = np.isin(data, list(green_areas))
            pbar.update(50)
            raster = np.zeros_like(data, dtype=np.uint8)
            raster[green_mask] = 1
            pbar.update(50)
            pbar.set_description("Green areas filtered")
            pbar.close()
            result = {
                "data": raster,
                "transform": transform,
                "crs": copernicus_crs,
                "shape": copernicus_shape
            }
            return result
