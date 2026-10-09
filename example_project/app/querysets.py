from __future__ import annotations

from django.db import models

__all__ = [
    "ProjectManager",
    "ProjectQuerySet",
    "TaskManager",
    "TaskQuerySet",
]


class ProjectQuerySet(models.QuerySet): ...


_ProjectManagerBase = models.Manager.from_queryset(ProjectQuerySet)


class ProjectManager(_ProjectManagerBase): ...


class TaskQuerySet(models.QuerySet): ...


_TaskManagerBase = models.Manager.from_queryset(TaskQuerySet)


class TaskManager(_TaskManagerBase): ...
