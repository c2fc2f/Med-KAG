"""
This module defines the `Tool` type alias, representing the various kinds of
executable units or utilities available to the Language Model.
"""

from typing import TypeAlias
from .function import ToolFunction

Tool: TypeAlias = ToolFunction[object]
