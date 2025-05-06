from abc import ABC, abstractmethod


class interface(ABC):
    """
    An abstract base class for utility functions related to geographical data.

    Methods
    -------
    get_land_use_percentages()
        Abstract method to calculate the land use percentages.
    """

    @abstractmethod
    def get_land_use_percentages(self) -> str:
        """
        Calculates the land use percentages.

        Returns
        -------
        str
            A JSON string containing the land use percentages, where keys are land use types and values are percentages.
        """
        pass
