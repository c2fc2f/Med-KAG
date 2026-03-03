from typing import Callable, TypeVar

T = TypeVar("T")


def compose(*functions: Callable[[T], T]) -> Callable[[T], T]:
    """
    Compose multiple functions into one (left to right execution).

    Parameters:
        *functions: Variable number of functions to compose.

    Returns:
        A new function that applies all functions in sequence.
    """

    def composed(temp: T) -> T:
        for func in functions:
            temp = func(temp)
        return temp

    return composed
