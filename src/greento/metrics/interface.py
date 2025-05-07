from abc import ABC, abstractmethod


class interface(ABC):
    """
    An abstract base class for calculating metrics using geographical data.

    Methods
    -------
    green_area_per_person()
        Abstract method to calculate the green area per person.
    get_isochrone_green(lat, lon, max_time, transport_mode)
        Abstract method to calculate the reachable green areas within a given time from a starting point.
    """

    @abstractmethod
    def green_area_per_person(self) -> str:
        """
        Calculates the green area per person.

        Returns
        -------
        str
            A JSON string containing the green area per person.
        """
        pass

    @abstractmethod
    def get_isochrone_green(
        self, lat: float, lon: float, max_time: float, transport_mode: str
    ) -> str:
        """
        Calculates the reachable green areas within a given time from a starting point.

        Parameters
        ----------
        lat : float
            The latitude of the starting point.
        lon : float
            The longitude of the starting point.
        max_time : float
            The maximum travel time in minutes.
        transport_mode : str
            The type of transport network (e.g., 'walk', 'bike', 'drive', 'all_public', 'drive_public').

        Returns
        -------
        str
            A JSON string containing the reachable green areas in the selected max time with the selected transport mode.
        """
        pass
