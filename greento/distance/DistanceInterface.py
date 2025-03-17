from abc import ABC, abstractmethod
class DistanceInterface(ABC):
    @abstractmethod
    def direction_to_green(self, lat, lon, transport_mode):
        pass
    @abstractmethod
    def get_nearest_green_position(self, lat, lon):
        pass