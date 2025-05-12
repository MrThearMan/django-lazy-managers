from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.db.models.manager import BaseManager
from django.utils.module_loading import import_string

from .typing import ManagerDeconstructArgs
from .utils import find_attribute_type_hint_path

if TYPE_CHECKING:
    from django.db import models
    from django.db.models import Manager
    from django.db.models.fields.related_descriptors import ManyToManyDescriptor, ReverseManyToOneDescriptor

__all__ = [
    "LazyModelManager",
]


class LazyModelManager(BaseManager):
    """
    Descriptor for lazily loading a model manager.
    Should always be used using `LazyModelManager.new()`.
    """

    @classmethod
    def new(cls) -> LazyModelManager:
        """
        Create a new lazy loaded model manager for a model.

        Example:

        >>> from typing import TYPE_CHECKING, ClassVar
        >>>
        >>> from django.db import models
        >>>
        >>> if TYPE_CHECKING:
        ...     from .queryset import MyModelManager  # type: ignore
        >>>
        >>> class MyModel(models.Model):
        ...     objects: ClassVar[MyModelManager] = LazyModelManager.new()

        Similarly to `LazyModelAttribute`, this descriptor is needed if 'MyModelManager' (or its queryset)
        contain imports from other models, so that importing it directly to the module might cause cyclical imports.

        Additionally, this class monkey-patches the model's managers, as well as the class attribute for the manager
        after the lazy loading is done, so that the lazy-loaded manager is used directly after it's loaded.
        """
        path = find_attribute_type_hint_path(depth=1)

        # Create a new subclass so that '__import_path__' is unique per lazy-loaded manager.
        class LazyManager(cls, __import_path__=path): ...

        return LazyManager()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        # '__import_path__' should be given to the initial subclass, but can be omitted if subclassed further.
        # (This is required for django-modeltranslation to work.)
        cls.__import_path__: str = kwargs.get("__import_path__") or cls.__import_path__
        """Import path to the type hint."""

        cls.__manager__: Manager | None = None
        """Type hinted Manager class imported from `__import_path__`."""

    def contribute_to_class(self, cls: type[models.Model], name: str) -> None:
        # Mirror the 'BaseManager.contribute_to_class' method,
        # but use our own '__get__' instead of 'ManagerDescriptor'.
        self.name = self.name or name
        self.model = cls
        setattr(cls, name, self)
        cls._meta.add_manager(self)  # type: ignore[arg-type]

    @property
    def use_in_migrations(self) -> bool:
        manager = self._load_manager()
        return manager.use_in_migrations

    def deconstruct(self) -> ManagerDeconstructArgs:
        # Replace the 'manager_class' argument so the actual manager class is loaded.
        # Skip some of the validation logic in the original method, as we don't need it here.
        return ManagerDeconstructArgs(
            as_manager=False,
            manager_class=self.__import_path__,
            qs_class=None,
            args=self._constructor_args[0],
            kwargs=self._constructor_args[1],
        )

    def __getattr__(self, item: str) -> Any:
        """Called if an attribute is not found in the class."""
        # Manager cannot be loaded until the module containing the model is loaded
        # 'model' exists if 'contribute_to_class' is called after the model is instantiated,
        # although this doesn't guarantee the module is loaded.
        if "model" not in self.__dict__:
            msg = f"{type(self).__name__} has no attribute {item!r}"
            raise AttributeError(msg)

        manager = self._load_manager()

        # If name doesn't exits, this is a call from a related manager.
        if self.name is None:
            manager = self._replace_related_manager(manager)
        else:
            self._replace_manager(manager, self.model, self.name)

        # Now check if the attribute exists.
        return getattr(manager, item)

    def _replace_related_manager(self, manager: Manager) -> Any:
        """Replace this related manager with a new related manager created from the lazy-loaded manager."""
        manager_name = self.__class__.__name__

        # Find the related model and related name for the manager.
        # We can match by the name, since related managers are always created using either
        # `django.db.models.fields.related_descriptors.create_reverse_many_to_one_manager` or
        # `django.db.models.fields.related_descriptors.create_forward_many_to_many_manager`
        if manager_name == "RelatedManager":
            related_model: type[models.Model] = self.field.remote_field.model
            related_name: str = self.field.remote_field.related_name

        elif manager_name == "ManyRelatedManager":
            related_model: type[models.Model] = self.source_field.remote_field.model
            related_name: str = self.prefetch_cache_name

        else:
            msg = f"Unknown related manager: {manager_name}"
            raise RuntimeError(msg)

        # Get the descriptor for the many-relation.
        descriptor: ReverseManyToOneDescriptor | ManyToManyDescriptor = getattr(related_model, related_name)

        # Set required attributes to the lazy-loaded manager and replace it in the model's options.
        manager.model = self.model
        manager.name = self.name = self.model._default_manager.name  # noqa: SLF001
        self._replace_manager(manager, self.model, self.name)

        # Clear this `cached_property` (if set) to force the related manager to be recreated when descriptor is used.
        if "related_manager_cls" in descriptor.__dict__:
            delattr(descriptor, "related_manager_cls")

        # Get the new related manager instance.
        return descriptor.__get__(self.instance, None)

    def __get__(self, instance: models.Model | None, model: type[models.Model]) -> Any:
        """Called if accessed from Model class."""
        manager = self._load_manager()
        self._replace_manager(manager, self.model, self.name)
        return getattr(self.model, self.name)

    def _load_manager(self) -> Manager:
        """Get the lazy-loaded manager."""
        cls = type(self)

        # Import the manager class if it hasn't been imported yet.
        if cls.__manager__ is None:
            manager_class = import_string(cls.__import_path__)
            cls.__manager__ = manager_class()

        return cls.__manager__

    def _replace_manager(self, manager: Manager, model: type[models.Model], name: str) -> None:
        """Replace this lazy manager with the actual manager in the model options manager list."""
        # Make a copy of the managers so that model inheritance doesn't break.
        local_managers = list(model._meta.local_managers)  # noqa: SLF001
        model._meta.local_managers = []  # noqa: SLF001

        # Only replace this manager with its lazy-loaded version, leave the rest as they are.
        for local_manager in local_managers:
            if name == local_manager.name:
                manager.contribute_to_class(model, name)
            else:
                model._meta.local_managers.append(local_manager)  # noqa: SLF001

        # Make managers immutable to avoid issues with model inheritance.
        model._meta.local_managers = model._meta.managers  # type: ignore[assignment]  # noqa: SLF001

    def __eq__(self, other: object) -> bool:
        manager = self._load_manager()
        return manager == other

    def __hash__(self) -> int:
        manager = self._load_manager()
        return hash(manager)
