from abc import ABC, abstractmethod
from typing import Any, Dict

class interface(ABC):
    """
    An abstract base class for processing green areas.

    Methods
    -------
    get_green(**kwargs)
        Abstract method to filter and process green areas.
    """

    @abstractmethod
    def get_green(self, **kwargs: Dict[str, Any]) -> Any:
        """
        Filters and processes green areas.

        Parameters
        ----------
        **kwargs : dict, optional
            Additional arguments to specify green areas.

        Returns
        -------
        Any
            The filtered green areas for the source selected.
        """
        pass
