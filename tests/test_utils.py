from __future__ import annotations

from unittest.mock import Mock

import pytest

from lazy_managers.utils import get_type_hint, get_type_hint_module_name


def caller_frame(*, line: int = 1) -> Mock:
    return Mock(f_lineno=line, f_locals={"__module__": "example_project.app.models"})


def test_get_type_hint() -> None:
    source_code = ["    objects: ProjectManager = LazyModelManager.new()"]

    assert get_type_hint(caller_frame(), source_code) == "ProjectManager"


def test_get_type_hint__wrapped() -> None:
    source_code = ["    objects: ClassVar[ProjectManager] = LazyModelManager.new()"]

    assert get_type_hint(caller_frame(), source_code) == "ProjectManager"


def test_get_type_hint_module_name__absolute() -> None:
    source_code = ["from example_project.app.querysets import ProjectManager"]

    module_name = get_type_hint_module_name("ProjectManager", caller_frame(), source_code)

    assert module_name == "example_project.app.querysets"


def test_get_type_hint_module_name__relative() -> None:
    source_code = ["    from .querysets import ProjectManager"]

    module_name = get_type_hint_module_name("ProjectManager", caller_frame(), source_code)

    assert module_name == "example_project.app.querysets"


def test_get_type_hint_module_name__relative__package() -> None:
    source_code = ["    from . import ProjectManager"]

    module_name = get_type_hint_module_name("ProjectManager", caller_frame(), source_code)

    assert module_name == "example_project.app"


def test_get_type_hint_module_name__relative__parent() -> None:
    source_code = ["    from ..app.querysets import ProjectManager"]

    module_name = get_type_hint_module_name("ProjectManager", caller_frame(), source_code)

    assert module_name == "example_project.app.querysets"


def test_get_type_hint_module_name__not_imported() -> None:
    source_code = ["from typing import ClassVar", "    objects: ClassVar[ProjectManager] = LazyModelManager.new()"]

    msg = "Unable to find import path for 'ProjectManager'."
    with pytest.raises(RuntimeError, match=msg):
        get_type_hint_module_name("ProjectManager", caller_frame(), source_code)
