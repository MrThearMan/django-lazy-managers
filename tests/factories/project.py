from __future__ import annotations

import datetime

import factory
from factory import LazyFunction

from example_project.app.models import Project

from ._base import GenericDjangoModelFactory, ReverseForeignKeyFactory

__all__ = [
    "ProjectFactory",
]


class ProjectFactory(GenericDjangoModelFactory[Project]):
    class Meta:
        model = Project
        skip_postgeneration_save = True

    name = factory.Faker("name")
    description = factory.Faker("text")
    created_at = LazyFunction(datetime.datetime.now)

    tasks = ReverseForeignKeyFactory("tests.factories.TaskFactory")  # type: ignore
