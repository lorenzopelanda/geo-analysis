from abc import ABC, abstractmethod

class UtilsInterface(ABC):
    @abstractmethod
    def get_land_use_percentages(self):
        pass

