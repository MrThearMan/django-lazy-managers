from __future__ import annotations

import ast
import inspect
import sys
from importlib.util import resolve_name

__all__ = [
    "find_attribute_type_hint_path",
    "find_import_path",
    "find_type_hint",
]

# Type hints that wrap the actual type hint, e.g. 'ClassVar[MyManager]'.
_WRAPPERS = frozenset({"ClassVar", "Final", "LazyAttribute"})


def find_attribute_type_hint_path(*, depth: int) -> str:
    """
    Perform some python black magic to find the dotted import path to where a class for an attribute's
    type hint is defined. This can be useful if class for the type hint cannot be imported directly to
    the module the attribute definition is, so its defined inside a 'TYPE_CHECKING' block.
    This function will find that import in the module's code, and determine the import path from it.

    :param depth: How many frames to go back from the caller frame to find the attribute definition.
    """
    frame = sys._getframe(depth + 1)  # noqa: SLF001
    source_code = "".join(inspect.findsource(frame)[0])
    module = ast.parse(source_code)
    type_hint = find_type_hint(module, line=frame.f_lineno)
    return find_import_path(type_hint, module, package=frame.f_globals.get("__package__") or "")


def find_type_hint(module: ast.Module, *, line: int) -> str:
    """Find the type hint for the annotated assignment on the given line in the module."""
    for node in ast.walk(module):
        if isinstance(node, ast.AnnAssign) and node.lineno <= line <= (node.end_lineno or node.lineno):
            return _type_hint_name(node.annotation)

    msg = f"Unable to find a type hint for the attribute on line {line}."
    raise RuntimeError(msg)


def _type_hint_name(node: ast.expr) -> str:
    """Get the dotted name of the class in the type hint, e.g., 'MyManager' from 'ClassVar[MyManager[MyModel]]'."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return _type_hint_name(ast.parse(node.value, mode="eval").body)

    if isinstance(node, ast.Subscript):
        name = _dotted_name(node.value)
        if name.rpartition(".")[2] in _WRAPPERS:
            return _type_hint_name(node.slice)
        return name

    return _dotted_name(node)


def _dotted_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        return f"{_dotted_name(node.value)}.{node.attr}"

    msg = f"Unsupported type hint: {ast.unparse(node)!r}. The type hint should be a single class."
    raise RuntimeError(msg)


def find_import_path(type_hint: str, module: ast.Module, *, package: str) -> str:
    """
    Find the import for the type hint in the module, and return the dotted import path to the type hint.

    :param type_hint: Dotted name of the type hint, e.g., 'MyManager' or 'managers.MyManager'.
    :param module: The module where the type hint is imported.
    :param package: The package of the module, used to resolve relative imports.
    """
    name, _, attribute = type_hint.partition(".")

    for node in ast.walk(module):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if (alias.asname or alias.name) == name:
                    module_name = resolve_name("." * node.level + (node.module or ""), package)
                    return ".".join(part for part in (module_name, alias.name, attribute) if part)

        elif isinstance(node, ast.Import):
            for alias in node.names:
                # 'import foo.bar as baz' binds 'baz' to 'foo.bar'.
                if alias.asname == name:
                    return ".".join(part for part in (alias.name, attribute) if part)
                # 'import foo.bar' binds 'foo', so the type hint already is the full path.
                if alias.asname is None and alias.name.partition(".")[0] == name:
                    return type_hint

    msg = f"Unable to find import path for {type_hint!r}. Make sure the type hint is imported in the module."
    raise RuntimeError(msg)
