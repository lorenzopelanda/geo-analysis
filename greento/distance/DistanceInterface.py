from abc import ABC, abstractmethod
class DistanceInterface(ABC):
    @abstractmethod
    def directions(self, lat, lon,start_lat, start_lon, transport_mode):
        pass
    @abstractmethod
    def get_nearest_green_position(self, lat, lon):
        pass