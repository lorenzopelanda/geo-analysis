from abc import ABC, abstractmethod

class UtilsInterface(ABC):
    """
    An abstract base class for utility functions related to geographical data.

    Methods:
    -------
    get_land_use_percentages():
        Abstract method to calculate the land use percentages.
    """
    @abstractmethod
    def get_land_use_percentages(self):
        """
        Calculates the land use percentages.

        Returns:
        -------
        Any
            The calculated land use percentages.
        """
        pass

