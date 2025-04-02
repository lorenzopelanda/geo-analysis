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

        Args:
            **kwargs: Additional arguments to specify green areas.

        Returns:
            Any: The filtered green areas for the source selected.
        """
        pass