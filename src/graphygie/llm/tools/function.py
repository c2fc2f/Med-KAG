"""
This module provides utilities to wrap and inspect Python functions as tools
consumable by an LLM. It defines structures to parse docstrings and generate
schemas (parameters, types, descriptions) required for function calling.
"""

from typing import Callable, Any, Literal
from docstring_parser import parse
from dataclasses import dataclass


@dataclass()
class Properties:
    """
    Represents the metadata for a single function parameter.

    Attributes:
    - type (str): The data type of the parameter (e.g., 'string', 'integer').
    - description (str): A natural language description of what the parameter
        represents.
    """

    type: str
    description: str


@dataclass()
class Parameters:
    """
    Represents the schema of a function's parameters, compatible with JSON
        Schema standards.

    Attributes:
    - properties (dict[str, Properties]): A dictionary mapping parameter names
        to their metadata.
    - required (list[str]): A list of parameter names that are mandatory.
    - type (Literal["object"]): The root type of the schema, defaults to
        "object".
    """

    properties: dict[str, Properties]
    required: list[str]
    type: Literal["object"] = "object"


class ToolFunction:
    """
    Wraps a standard Python function to expose its metadata (name,
    description, parameters) dynamically by parsing its docstring.
    """

    def __init__(self, func: Callable) -> None:
        """
        Initializes the ToolFunction by parsing the docstring of the provided
        function.

        Parameters:
        - func (Callable): The original function to wrap.
        """
        self._func = func
        self._doc = parse(self._func.__doc__ or "")

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        """
        Executes the underlying wrapped function.

        Parameters:
        - *args: Positional arguments passed to the function.
        - **kwds: Keyword arguments passed to the function.

        Returns:
        - Any: The result returned by the wrapped function.
        """
        return self._func(*args, **kwds)

    @property
    def description(self) -> str:
        """
        Retrieves the detailed description of the function from its docstring.

        Returns:
        - str: The long description extracted from the docstring.
        """
        return self._doc.long_description or ""

    @property
    def name(self) -> str:
        """
        Retrieves the name of the function.

        Returns:
        - str: The identifier name of the function.
        """
        return self._func.__name__

    @property
    def parameters(self) -> Parameters:
        """
        Constructs the parameter schema by extracting argument details
        from the parsed docstring.

        Returns:
        - Parameters: A structured object containing parameter types,
            descriptions, and requirements.
        """
        return Parameters(
            {
                param.arg_name: Properties(
                    param.type_name or "", param.description or ""
                )
                for param in self._doc.params
            },
            [param.arg_name for param in self._doc.params if not param.is_optional],
        )


def tool(func: Callable) -> ToolFunction:
    """
    Decorator that converts a standard Python function into a ToolFunction instance,
    enabling it to be used within the tool ecosystem.

    Parameters:
    - func (Callable): The function to decorate.

    Returns:
    - ToolFunction: The wrapped tool function.
    """
    return ToolFunction(func)
