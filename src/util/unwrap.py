from typing import TypeVar

T = TypeVar("T")


def unwrap(value: T | None) -> T:
    """
    Returns the given string if it is not None, otherwise raises a ValueError.

    Parameters:
    - value (str | None): The string to unwrap.

    Returns:
    - str: The unwrapped string if it is not None.

    Raises:
    - ValueError: If the value is None.
    """
    if value is None:
        raise ValueError("called `unwrap()` on a `None` value")
    return value


def unwrap_or(value: T | None, default: T) -> T:
    """
    Returns the given value if it is not None,
    otherwise returns the provided default value.

    Parameters:
    - value (T | None): The optional value to check.
    - default (T): The fallback value if 'value' is None.

    Returns:
    - T: The unwrapped value or the default.
    """
    return value if value is not None else default
