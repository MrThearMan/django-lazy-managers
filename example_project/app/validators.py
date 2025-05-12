from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError

if TYPE_CHECKING:
    from .models import Project, Task


@dataclasses.dataclass(frozen=True, slots=True)
class ProjectValidators:
    project: Project

    def validate_name(self, value: str) -> None:
        if not value:
            msg = "Invalid name"
            raise ValidationError(msg)

    @classmethod
    def validate_creation(cls, name: str) -> None:
        if not name:
            msg = "Invalid name"
            raise ValidationError(msg)


@dataclasses.dataclass(frozen=True, slots=True)
class TaskValidators:
    task: Task

    def validate_name(self, value: str) -> None:
        if not value:
            msg = "Invalid name"
            raise ValidationError(msg)

    @classmethod
    def validate_creation(cls, name: str) -> None:
        if not name:
            msg = "Invalid name"
            raise ValidationError(msg)
