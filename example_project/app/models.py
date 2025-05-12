from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from django.db import models

from lazy_managers import LazyModelAttribute, LazyModelManager

if TYPE_CHECKING:
    from .querysets import ProjectManager, TaskManager
    from .validators import ProjectValidators, TaskValidators

__all__ = [
    "Project",
    "Task",
]


class Project(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    tasks: TaskManager

    objects: ClassVar[ProjectManager] = LazyModelManager.new()
    validators: ClassVar[ProjectValidators] = LazyModelAttribute.new()

    def __str__(self) -> str:
        return self.name


class Task(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")

    objects: ClassVar[TaskManager] = LazyModelManager.new()
    validators: ClassVar[TaskValidators] = LazyModelAttribute.new()

    def __str__(self) -> str:
        return self.name
