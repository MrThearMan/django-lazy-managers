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
def test_lazy_manager__load__multiple_managers() -> None:
    class Item(models.Model):
        objects: ClassVar[ProjectManager] = LazyModelManager.new()
        other = models.Manager()

        class Meta:
            app_label = "app"

    assert Item._meta.default_manager.name == "objects"

    assert isinstance(Item.objects, ProjectManager)
    assert [manager.name for manager in Item._meta.managers] == ["objects", "other"]
    assert Item._meta.default_manager.name == "objects"
    assert type(Item.other) is models.Manager


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
def test_lazy_manager__load__reverse_foreign_key__multiple_instances() -> None:
    class Parent(models.Model):
        class Meta:
            app_label = "app"

    class Child(models.Model):
        objects: ClassVar[ProjectManager] = LazyModelManager.new()
        parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name="children")

        class Meta:
            app_label = "app"

    # Both related managers are created before the lazy manager is loaded.
    first = Parent(pk=1).children
    second = Parent(pk=2).children

    assert isinstance(first.all(), ProjectQuerySet)
    assert isinstance(second.all(), ProjectQuerySet)


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
