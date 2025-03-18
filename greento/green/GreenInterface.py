from abc import ABC, abstractmethod

class GreenInterface(ABC):
    @abstractmethod
    def get_green(self, **kwargs):
        pass