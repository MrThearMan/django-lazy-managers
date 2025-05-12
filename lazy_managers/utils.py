from __future__ import annotations

import inspect
import re
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import FrameType

__all__ = [
    "find_attribute_type_hint_path",
    "get_type_hint",
    "get_type_hint_module_name",
]

_WRAPPER_PATTERN = re.compile(r".+\[(?P<type_hint>.+)]$")


def find_attribute_type_hint_path(*, depth: int) -> str:
    """
    Perform some python black magic to find the dotted import path to where a class for an attribute's
    type hint is defined. This can be useful if class for the type hint cannot be imported directly to
    the module the attribute definition is, so its defined inside a 'TYPE_CHECKING' block.
    This function will find that import in the module's code, and determine the import path from it.

    Note that the class attribute and the import should both be defined on a single line for this to work.

    :param depth: How many frames to go back from the caller frame to find the attribute definition.
    """
    frame: FrameType = sys._getframe(depth + 1)  # noqa: SLF001
    source_code = inspect.findsource(frame)[0]
    type_hint = get_type_hint(frame, source_code)
    module_name = get_type_hint_module_name(type_hint, frame, source_code)
    return f"{module_name}.{type_hint}"


def get_type_hint(frame: FrameType, source_code: list[str]) -> str:
    """Get the type hint for the attribute this descriptor defined for."""
    current_line = source_code[frame.f_lineno - 1]
    definition = current_line.split("=", maxsplit=1)[0]
    def_and_type_hint = definition.split(":", maxsplit=1)
    type_hint = def_and_type_hint[1].strip()
    match = _WRAPPER_PATTERN.match(type_hint)
    if match is not None:
        type_hint = match.group("type_hint")
    return type_hint


def get_type_hint_module_name(type_hint: str, frame: FrameType, source_code: list[str]) -> str:
    """
    Go through the source code for the caller frame to find the line where the type hint
    is imported. Note that the import should be defined on a single line for this to work.
    """
    module_name: str | None = None
    for line in source_code:
        if type_hint in line and "import" in line:
            module_name = line.strip().removeprefix("from").split("import")[0].strip()
            break

    if module_name is None:
        msg = (
            f"Unable to find import path for {type_hint!r}. "
            f"Make sure import for the attribute's type hint is defined on a single line."
        )
        raise RuntimeError(msg)

    # Handle relative imports
    if module_name.startswith("."):
        caller_module: str = frame.f_locals["__module__"]

        # Remove number parts in the caller module equal to the number of relative "dots" in the import
        module_parts = caller_module.split(".")
        for part in module_name.split("."):
            if part:
                break
            module_parts.pop()

        module_name = ".".join(module_parts) + module_name

    return module_name
