from abc import ABC, abstractmethod

class MetricsInterface(ABC):
    """
    An abstract base class for calculating metrics using geographical data.

    Methods:
    -------
    green_area_per_person():
        Abstract method to calculate the green area per person.
    get_isochrone_green(lat, lon, max_time, transport_mode):
        Abstract method to calculate the reachable green areas within a given time from a starting point.
    """

    @abstractmethod
    def green_area_per_person(self):
        """
        Calculates the green area per person.

        Returns:
        -------
        Any
            The calculated green area per person.
        """
        pass

    @abstractmethod
    def get_isochrone_green(self, lat, lon, max_time, transport_mode):
        """
        Calculates the reachable green areas within a given time from a starting point.

        Parameters:
        ----------
        lat : float
            The latitude of the starting point.
        lon : float
            The longitude of the starting point.
        max_time : float
            The maximum travel time in minutes.
        transport_mode : str
            The type of transport network (e.g., 'walk', 'bike', 'drive', 'all_public', 'drive_public').

        Returns:
        -------
        Any
            The calculated reachable green areas and related metrics.
        """
        pass