from __future__ import annotations

from typing import Any

from django.utils.module_loading import import_string

from .utils import find_attribute_type_hint_path

__all__ = [
    "LazyModelAttribute",
]


class LazyModelAttribute:
    """
    Descriptor for accessing an attribute on a Model lazily based on a type hint.
    Should always be used using `LazyModelAttribute.new()`.
    """

    @classmethod
    def new(cls) -> LazyModelAttribute:
        """
        Create a new lazy loaded model attribute for a model.

        Example:

        >>> from typing import TYPE_CHECKING
        >>>
        >>> from django.db import models
        >>>
        >>> if TYPE_CHECKING:
        ...     from .validators import MyModelValidator  # type: ignore
        >>>
        >>> class MyModel(models.Model):
        ...     validators: MyModelValidator = LazyModelAttribute.new()

        Here 'MyModelValidator' is a class that includes validation logic for the model.
        It takes a single argument, which is the model instance begin validated,
        which is the interface required for this descriptor.

        This descriptor is needed because 'MyModelValidator' contains imports from
        other models, so importing it directly to the module might cause cyclical imports.
        That's why it is imported in a 'TYPE_CHECKING' block and only added as a type hint
        for the 'LazyModelAttribute', which can then lazily import the validator when it is first accessed.

        'LazyModelAttribute' differs from properties by also allowing class-level access. Accessing the
        attribute on the class level will return the hinted class itself, which in the validator example will
        allow create validation using classmethods.

        Due to limitations of the Python typing system, the returned type on the class-level will be
        an instance of the typed class, but the actual return value is the hinted class itself.

        This approach is used instead of a more conventional 'decorator-descriptor' approach because
        some type checkers (PyCharm in particular) do not infer types from 'decorator-descriptors'
        correctly (at least when this was written).
        """
        path = find_attribute_type_hint_path(depth=1)

        # Create a new subclass so that '__import_path__' is unique per lazy-loaded manager.
        class LazyAttribute(cls, __import_path__=path): ...

        return LazyAttribute()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        # '__import_path__' should always be given.
        cls.__import_path__: str = kwargs["__import_path__"]
        """Import path to the type hint."""

        cls.__attribute_class__: type | None = None
        """Type hinted class imported from `__import_path__`."""

    def __get__(self, instance: Any | None, owner: type[Any]) -> Any:
        attribute_class = self.__load_class()
        if instance is None:
            return attribute_class
        return attribute_class(instance)

    def __load_class(self) -> type:
        """Get the lazy-loaded class."""
        cls = type(self)

        # Import the type hint class if it hasn't been imported yet.
        if cls.__attribute_class__ is None:
            cls.__attribute_class__ = import_string(cls.__import_path__)

        return cls.__attribute_class__
