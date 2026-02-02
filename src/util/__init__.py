"""
This module aggregates utility functions for file reading, string unwrapping,
, cleaner string and template-based prompt generation.
"""

from .read_to_string import read_to_string
from .unwrap import unwrap, unwrap_or
from .cleaner import strip_code_fences, strip_after_double_newline
from .compose import compose
from .user_prompt import user_prompt
from .generator_system_prompt import generator_system_prompt


__all__: list[str] = [
    "read_to_string",
    "unwrap",
    "unwrap_or",
    "user_prompt",
    "generator_system_prompt",
    "strip_code_fences",
    "strip_after_double_newline",
    "compose",
]
