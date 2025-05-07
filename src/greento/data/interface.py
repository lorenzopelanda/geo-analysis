from abc import ABC, abstractmethod
from typing import Any
from greento.boundingbox import boundingbox


class interface(ABC):
    """
    An abstract base class for data downloaders.

    Methods
    -------
    get_data(bounding_box)
        Abstract method to download and process data for the given bounding box.
    """

    @abstractmethod
    def get_data(self, bounding_box: "boundingbox") -> Any:
        """
        Downloads and processes data for the given bounding box.

        Parameters
        ----------
        bounding_box : BoundingBox
            The bounding box for which to download data.

        Returns
        -------
        Any
            The downloaded and processed data.
        """
        pass
