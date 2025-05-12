from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar
from unittest import mock

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import TracebackType
    from unittest.mock import NonCallableMock

__all__ = [
    "patch_method",
]

T = TypeVar("T")
P = ParamSpec("P")


class patch_method:  # noqa: N801
    """
    Patch a method inside a class.

    Used in place of 'mock.patch' to have the 'method' argument as a function instead of a string.
    Does not work on functions declared outside of classes.

    >>> @patch_method(MyClass.my_method, return_value=...)
    >>> def test_something(...):
    >>>     ...

    or

    >>> @patch_method(MyClass.my_method)
    >>> def test_something(...):
    >>>     MyClass.my_method.return_value = ...
    >>>     ...

    or

    >>> def test_something(...):
    >>>     with patch_method(MyClass.my_method, return_value=...):
    >>>         ...
    """

    def __init__(self, method: Callable, return_value: Any = None, side_effect: Any = None) -> None:
        # Get the full path to the method, e.g., 'module.submodule.Class.method'
        method_path = method.__module__ + "." + method.__qualname__  # type: ignore[attr-defined]
        self.patch = mock.patch(method_path, return_value=return_value, side_effect=side_effect)

    def __call__(self, func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Run the test with the method patched
            with self.patch:
                return func(*args, **kwargs)

        return wrapper

    def __enter__(self) -> NonCallableMock:
        return self.patch.__enter__()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        return self.patch.__exit__(exc_type, exc_val, exc_tb)
