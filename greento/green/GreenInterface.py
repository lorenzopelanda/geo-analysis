from abc import ABC, abstractmethod

class GreenInterface(ABC):
    @abstractmethod
    def get_green_area(self, **kwargs):
        pass