from abc import ABC, abstractmethod

class DownloaderInterface(ABC):
    @abstractmethod
    def get_data(self, bounding_box):
        pass
class UtilsInterface(ABC):
    @abstractmethod
    def get_green_area(self, **kwargs):
        pass

    @abstractmethod
    def get_land_use_percentages(self):
        pass
class GreenInterface(ABC):
    @abstractmethod
    def direction_to_green(self, lat, lon, transport_mode):
        pass
    @abstractmethod
    def get_nearest_green_position(self, lat, lon):
        pass
    @abstractmethod
    def green_area_per_person(self):
        pass
    @abstractmethod
    def get_isochrone_green(self, lat, lon, max_time, transport_mode):
        pass