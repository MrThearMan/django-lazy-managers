from __future__ import annotations

from django.db import models

__all__ = [
    "ProjectManager",
    "ProjectQuerySet",
    "TaskManager",
    "TaskQuerySet",
]


class ProjectQuerySet(models.QuerySet): ...


class ProjectManager(models.Manager.from_queryset(ProjectQuerySet)): ...


class TaskQuerySet(models.QuerySet): ...


class TaskManager(models.Manager.from_queryset(TaskQuerySet)): ...
