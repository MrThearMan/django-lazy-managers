from __future__ import annotations

from typing import Any
from unittest.mock import patch

from django.db import models
from django.utils.module_loading import import_string

from example_project.app.models import Project
from example_project.app.validators import ProjectValidators
from lazy_managers import LazyModelAttribute
from tests.helpers import patch_method

DESCRIPTOR = LazyModelAttribute.__get__


def clear_cache(self: LazyModelAttribute, instance: models.Model | None, owner: type[models.Model]) -> Any:
    # Remove cached attribute class
    type(self).__attribute_class__ = None
    return DESCRIPTOR(self, instance, owner)


def test_lazy_attribute__load__class() -> None:
    with (
        patch("lazy_managers.attribute.import_string", side_effect=import_string) as mock,
        patch_method(LazyModelAttribute.__get__, side_effect=clear_cache),
    ):
        validators = Project.validators

    mock.assert_called_once_with("example_project.app.validators.ProjectValidators")

    assert issubclass(validators, ProjectValidators)  # type: ignore[arg-type]


def test_lazy_attribute__load__instance() -> None:
    with (
        patch("lazy_managers.attribute.import_string", side_effect=import_string) as mock,
        patch_method(LazyModelAttribute.__get__, side_effect=clear_cache),
    ):
        validators = Project().validators

    mock.assert_called_once_with("example_project.app.validators.ProjectValidators")

    assert isinstance(validators, ProjectValidators)
