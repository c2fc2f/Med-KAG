"""
This module defines the abstract interface for objects capable of
representing and transmitting information.
"""

from abc import ABC, abstractmethod
from util.serializable import Serializable


class Info(ABC):
    """
    Abstract base class for objects that represent and send information.
    """

    @abstractmethod
    def info(self) -> dict[str, Serializable] | None:
        """
        Returns a dictionary of statistics from the most recent information
        transmission.
        """
        ...
