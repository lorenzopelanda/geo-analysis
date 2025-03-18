from abc import ABC, abstractmethod

class GreenInterface(ABC):
    """
    An abstract base class for processing green areas.

    Methods:
    -------
    get_green(**kwargs):
        Abstract method to filter and process green areas.
    """
    @abstractmethod
    def get_green(self, **kwargs):
        """
        Filters and processes green areas.

        Parameters:
        ----------
        **kwargs : dict, optional
            Additional arguments to specify green areas.

        Returns:
        -------
        dict
            A dictionary containing the filtered green areas, transform, CRS, and shape.
        """
        pass