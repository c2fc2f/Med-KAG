"""
This module defines the abstract interface for objects capable of
representing and transmitting information.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class Info(ABC):
    """
    Abstract base class for objects that represent and send information.
    """

    @abstractmethod
    def info(self) -> Optional[dict[str, Any]]:
        """
        Returns a dictionary of statistics from the most recent information
        transmission.
        """
        ...
