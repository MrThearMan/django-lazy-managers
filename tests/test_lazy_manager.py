from __future__ import annotations

from typing import Any, ClassVar
from unittest.mock import patch

import pytest
from django.db import models
from django.test.utils import isolate_apps
from django.utils.module_loading import import_string

from example_project.app.models import Project
from example_project.app.querysets import ProjectManager, ProjectQuerySet, TaskQuerySet
from lazy_managers import LazyModelManager
from tests.factories import ProjectFactory
from tests.helpers import patch_method

DESCRIPTOR = LazyModelManager.__get__


def clear_cache(self: LazyModelManager, instance: models.Model | None, owner: type[models.Model]) -> Any:
    # Remove cached manager class
    type(self).__manager__ = None
    return DESCRIPTOR(self, instance, owner)


def test_lazy_manager__load() -> None:
    with (
        patch("lazy_managers.manager.import_string", side_effect=import_string),
        patch_method(LazyModelManager.__get__, side_effect=clear_cache),
    ):
        manager = Project.objects

    assert isinstance(manager, ProjectManager)


@pytest.mark.django_db
def test_lazy_manager__load__related() -> None:
    project = ProjectFactory.create(tasks__name="Test")

    with (
        patch("lazy_managers.manager.import_string", side_effect=import_string),
        patch_method(LazyModelManager.__get__, side_effect=clear_cache),
    ):
        manager = project.tasks.all()

    assert isinstance(manager, TaskQuerySet)


@isolate_apps("example_project.app")
def test_lazy_manager__load__reverse_foreign_key__no_related_name() -> None:
    class Parent(models.Model):
        class Meta:
            app_label = "app"

    class Child(models.Model):
        objects: ClassVar[ProjectManager] = LazyModelManager.new()
        parent = models.ForeignKey(Parent, on_delete=models.CASCADE)

        class Meta:
            app_label = "app"

    queryset = Parent(pk=1).child_set.all()

    assert isinstance(queryset, ProjectQuerySet)


@isolate_apps("example_project.app")
def test_lazy_manager__load__reverse_many_to_many() -> None:
    class Item(models.Model):
        class Meta:
            app_label = "app"

    class Tag(models.Model):
        objects: ClassVar[ProjectManager] = LazyModelManager.new()
        items = models.ManyToManyField(Item, related_name="tags")

        class Meta:
            app_label = "app"

    queryset = Item(pk=1).tags.all()

    assert isinstance(queryset, ProjectQuerySet)


@isolate_apps("example_project.app")
def test_lazy_manager__load__reverse_many_to_many__no_related_name() -> None:
    class Item(models.Model):
        class Meta:
            app_label = "app"

    class Tag(models.Model):
        objects: ClassVar[ProjectManager] = LazyModelManager.new()
        items = models.ManyToManyField(Item)

        class Meta:
            app_label = "app"

    queryset = Item(pk=1).tag_set.all()

    assert isinstance(queryset, ProjectQuerySet)
