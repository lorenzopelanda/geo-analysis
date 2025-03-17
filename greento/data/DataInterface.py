from abc import ABC, abstractmethod
class DownloaderInterface(ABC):
    @abstractmethod
    def get_data(self, bounding_box):
        pass