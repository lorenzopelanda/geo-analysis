from abc import ABC, abstractmethod
from typing import Any


class interface(ABC):
    """
    An abstract base class for calculating distances and directions.

    Methods
    -------
    directions(lat, lon, start_lat, start_lon, transport_mode)
        Calculates the shortest path and estimated travel time between two points.
    get_nearest_green_position(lat, lon)
        Finds the nearest green area from a given starting point.
    """

    @abstractmethod
    def directions(
        self,
        lat: float,
        lon: float,
        start_lat: float,
        start_lon: float,
        transport_mode: str,
    ) -> Any:
        """
        Calculates the shortest path and estimated travel time between two points.

        Parameters
        ----------
        lat : float
            Latitude of the destination point.
        lon : float
            Longitude of the destination point.
        start_lat : float
            Latitude of the starting point.
        start_lon : float
            Longitude of the starting point.
        transport_mode : str
            Mode of transport (e.g., "walk", "bike", "drive").

        Returns
        -------
        Any
            The calculated directions and travel time.
        """
        pass

    @abstractmethod
    def get_nearest_green_position(self, lat: float, lon: float) -> Any:
        """
        Finds the nearest green area from a given starting point.

        Parameters
        ----------
        lat : float
            Latitude of the starting point.
        lon : float
            Longitude of the starting point.

        Returns
        -------
        Any
            The nearest green position.
        """
        pass
