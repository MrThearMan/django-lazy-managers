from __future__ import annotations

from typing import TYPE_CHECKING, Any, NamedTuple, Protocol, overload

if TYPE_CHECKING:
    from django.db import models

__all__ = [
    "LazyAttribute",
    "ManagerDeconstructArgs",
]


class ManagerDeconstructArgs(NamedTuple):
    """Arguments for `BaseManager.deconstruct`."""

    as_manager: bool
    manager_class: str
    qs_class: type[models.QuerySet] | None
    args: tuple[Any, ...]
    kwargs: dict[str, Any]


class LazyAttribute[T](Protocol):
    """
    Type hint for a 'LazyModelAttribute'. Accessing the attribute from the
    model class gives the hinted class, and from a model instance gives an
    instance of the hinted class.
    """

    @overload
    def __get__(self, instance: None, owner: Any) -> type[T]: ...

    @overload
    def __get__(self, instance: object, owner: Any) -> T: ...
