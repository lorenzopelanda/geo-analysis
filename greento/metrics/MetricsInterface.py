from abc import ABC, abstractmethod
class MetricsInterface(ABC):
    @abstractmethod
    def green_area_per_person(self):
        pass
    @abstractmethod
    def get_isochrone_green(self, lat, lon, max_time, transport_mode):
        pass