from abc import ABC, abstractmethod
class DistanceInterface(ABC):
    """
    An abstract base class for calculating distances and directions.
    """
    @abstractmethod
    def directions(self, lat, lon,start_lat, start_lon, transport_mode):
        """
        Calculates the shortest path and estimated travel time between two points.

        Args:
            lat (float): Latitude of the destination point.
            lon (float): Longitude of the destination point.
            start_lat (float): Latitude of the starting point.
            start_lon (float): Longitude of the starting point.
            transport_mode (str): Mode of transport (e.g., "walk", "bike", "drive").

        Returns:
            Any: The calculated directions and travel time.
        """
        pass
    @abstractmethod
    def get_nearest_green_position(self, lat, lon):
        """
        Finds the nearest green area from a given starting point.

        Args:
            lat (float): Latitude of the starting point.
            lon (float): Longitude of the starting point.

        Returns:
            Any: The nearest green position.
        """
        pass