from __future__ import annotations

from typing import TYPE_CHECKING, Any, NamedTuple

if TYPE_CHECKING:
    from django.db import models

__all__ = [
    "ManagerDeconstructArgs",
]


class ManagerDeconstructArgs(NamedTuple):
    """Arguments for `BaseManager.deconstruct`."""

    as_manager: bool
    manager_class: str
    qs_class: type[models.QuerySet] | None
    args: tuple[Any, ...]
    kwargs: dict[str, Any]
