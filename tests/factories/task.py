from __future__ import annotations

import datetime

import factory
from factory import LazyFunction

from example_project.app.models import Task

from ._base import ForeignKeyFactory, GenericDjangoModelFactory

__all__ = [
    "TaskFactory",
]


class TaskFactory(GenericDjangoModelFactory[Task]):
    class Meta:
        model = Task

    name = factory.Faker("name")
    description = factory.Faker("text")
    created_at = LazyFunction(datetime.datetime.now)

    project = ForeignKeyFactory("tests.factories.ProjectFactory")  # type: ignore
