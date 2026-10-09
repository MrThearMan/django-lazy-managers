from __future__ import annotations

import ast

import pytest

from lazy_managers.utils import find_import_path, find_type_hint


def type_hint(source_code: str, *, line: int = 1) -> str:
    return find_type_hint(ast.parse(source_code), line=line)


def import_path(type_hint: str, source_code: str) -> str:
    return find_import_path(type_hint, ast.parse(source_code), package="example_project.app")


@pytest.mark.parametrize(
    ("annotation", "expected"),
    [
        ("ProjectManager", "ProjectManager"),
        ("ClassVar[ProjectManager]", "ProjectManager"),
        ("typing.ClassVar[ProjectManager]", "ProjectManager"),
        ("ClassVar[ProjectManager[Project]]", "ProjectManager"),
        ("ProjectManager[Project]", "ProjectManager"),
        ("Final[ProjectManager]", "ProjectManager"),
        ("LazyAttribute[ProjectValidators]", "ProjectValidators"),
        ("querysets.ProjectManager", "querysets.ProjectManager"),
        ("ClassVar[querysets.ProjectManager[Project]]", "querysets.ProjectManager"),
        ("'ClassVar[ProjectManager]'", "ProjectManager"),
    ],
)
def test_find_type_hint(annotation, expected) -> None:
    assert type_hint(f"objects: {annotation} = LazyModelManager.new()") == expected


def test_find_type_hint__multiple_lines() -> None:
    source_code = "objects: ClassVar[\n    ProjectManager\n] = (\n    LazyModelManager.new()\n)"

    assert type_hint(source_code, line=4) == "ProjectManager"


def test_find_type_hint__no_annotation() -> None:
    msg = "Unable to find a type hint for the attribute on line 1."
    with pytest.raises(RuntimeError, match=msg):
        type_hint("objects = LazyModelManager.new()")


def test_find_type_hint__unsupported() -> None:
    msg = "Unsupported type hint: 'ProjectManager | None'. The type hint should be a single class."
    with pytest.raises(RuntimeError, match=msg):
        type_hint("objects: ProjectManager | None = LazyModelManager.new()")


@pytest.mark.parametrize(
    ("type_hint_", "source_code", "expected"),
    [
        ("ProjectManager", "from example_project.app.querysets import ProjectManager", "example_project.app.querysets.ProjectManager"),
        ("ProjectManager", "from .querysets import ProjectManager", "example_project.app.querysets.ProjectManager"),
        ("ProjectManager", "from . import ProjectManager", "example_project.app.ProjectManager"),
        ("ProjectManager", "from ..app.querysets import ProjectManager", "example_project.app.querysets.ProjectManager"),
        ("PM", "from .querysets import ProjectManager as PM", "example_project.app.querysets.ProjectManager"),
        ("ProjectManager", "from .querysets import (\n    ProjectQuerySet,\n    ProjectManager,\n)", "example_project.app.querysets.ProjectManager"),
        ("querysets.ProjectManager", "from . import querysets", "example_project.app.querysets.ProjectManager"),
        ("qs.ProjectManager", "import example_project.app.querysets as qs", "example_project.app.querysets.ProjectManager"),
        ("example_project.app.querysets.ProjectManager", "import example_project.app.querysets", "example_project.app.querysets.ProjectManager"),
        ("qs", "import example_project.app.querysets as qs", "example_project.app.querysets"),
        ("ProjectManager", "if TYPE_CHECKING:\n    from .querysets import ProjectManager", "example_project.app.querysets.ProjectManager"),
    ],
)
def test_find_import_path(type_hint_, source_code, expected) -> None:
    assert import_path(type_hint_, source_code) == expected


def test_find_import_path__no_substring_match() -> None:
    source_code = "from .querysets import ProjectManager\nfrom .managers import Manager"

    assert import_path("Manager", source_code) == "example_project.app.managers.Manager"


def test_find_import_path__other_imports() -> None:
    source_code = "import os\nimport django.db as db\nfrom .querysets import ProjectManager"

    assert import_path("ProjectManager", source_code) == "example_project.app.querysets.ProjectManager"


def test_find_import_path__not_imported() -> None:
    source_code = "from typing import ClassVar"

    msg = "Unable to find import path for 'ProjectManager'. Make sure the type hint is imported in the module."
    with pytest.raises(RuntimeError, match=msg):
        import_path("ProjectManager", source_code)
