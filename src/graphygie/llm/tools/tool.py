"""
This module defines the `Tool` type alias, representing the various kinds of
executable units or utilities available to the Language Model.
"""

from typing import Union
from .function import ToolFunction


Tool = Union[ToolFunction]
