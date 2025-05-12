from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from django.contrib.contenttypes.fields import GenericForeignKey
from django.db.models import Model
from factory import FactoryError, PostGeneration
from factory.base import BaseFactory
from factory.declarations import SubFactory
from factory.django import DjangoModelFactory
from factory.utils import import_object

if TYPE_CHECKING:
    from collections.abc import Iterable

    from factory.builder import BuildStep, Resolver

__all__ = [
    "ForeignKeyFactory",
    "ForwardOneToOneFactory",
    "GenericDjangoModelFactory",
    "ManyToManyFactory",
    "ReverseForeignKeyFactory",
    "ReverseOneToOneFactory",
]

T = TypeVar("T")
FactoryType = str | type[BaseFactory] | Callable[[], type[BaseFactory]]
TModel = TypeVar("TModel", bound=Model)


# --- Generic factories --------------------------------------------------------------------------------------------


class GenericDjangoModelFactory(DjangoModelFactory, Generic[TModel]):
    """
    DjangoModelFactory that adds return type annotations for the
    `build`, `create`, `build_batch`, and `create_batch` methods,
    as well as some convenience methods for creating custom builder-methods.
    """

    @classmethod
    def build(cls: type[Generic[TModel]], **kwargs: Any) -> TModel:  # type: ignore
        return super().build(**kwargs)  # type: ignore

    @classmethod
    def create(cls: type[Generic[TModel]], **kwargs: Any) -> TModel:  # type: ignore
        return super().create(**kwargs)  # type: ignore

    @classmethod
    def build_batch(cls: type[Generic[TModel]], size: int, **kwargs: Any) -> list[TModel]:  # type: ignore
        return super().build_batch(size, **kwargs)  # type: ignore

    @classmethod
    def create_batch(cls: type[Generic[TModel]], size: int, **kwargs: Any) -> list[TModel]:  # type: ignore
        return super().create_batch(size, **kwargs)  # type: ignore


# --- Custom wrappers --------------------------------------------------------------------------------------------


class CustomFactoryWrapper:
    def __init__(self, factory_: FactoryType) -> None:
        self.factory: type[BaseFactory] | None = None
        self.callable: Callable[..., type[BaseFactory]] | None = None

        if isinstance(factory_, type) and issubclass(factory_, BaseFactory):
            self.factory = factory_
            return

        if callable(factory_):
            self.callable = factory_  # type: ignore
            return

        if not (isinstance(factory_, str) and "." in factory_):  # pragma: no cover
            msg = (
                "The factory must be one of: "
                "1) a string with the format 'module.path.FactoryClass' "
                "2) a Factory class "
                "3) a callable that returns a Factory class"
            )
            raise FactoryError(msg)

        self.callable = lambda: import_object(*factory_.rsplit(".", 1))

    def get(self) -> FactoryType:
        if self.factory is None:
            self.factory = self.callable()  # type: ignore
        return self.factory


# --- Related factories --------------------------------------------------------------------------------------------


class PostFactory(PostGeneration, Generic[TModel]):
    def __init__(self, factory: FactoryType) -> None:
        super().__init__(function=self.generate)
        self.field_name: str = ""
        self.factory_wrapper = CustomFactoryWrapper(factory)

    def __set_name__(self, owner: Any, name: str) -> None:
        """Set the name of the field in the factory this is in."""
        self.field_name = name

    def get_factory(self) -> BaseFactory:
        return self.factory_wrapper.get()  # type: ignore

    def generate(self, instance: Model, create: bool, models: Iterable[TModel] | None, **kwargs: Any) -> None: ...

    def manager(self, instance: Model) -> Any:
        """
        Find the related manager for the instance based on the field name it was defined with on the factory.

        Note that due to how Django handles related fields, the manager type is created dynamically at runtime.

        For one-to-many fields:
        - django.db.models.fields.related_descriptors.create_reverse_many_to_one_manager -> RelatedManager
        For many-to-many fields:
        - django.db.models.fields.related_descriptors.create_forward_many_to_many_manager -> ManyRelatedManager
        """
        return getattr(instance, self.field_name)


class ForeignKeyFactory(SubFactory, Generic[TModel]):
    """
    Factory for forward 'many-to-one' (foreign key) related fields.

    Basically the same as a SubFactory, but will not create a related object if:
    1. The relation can be null AND
    2. The related instance is not specified OR it's specified as 'None' AND
    3. The 'required' argument on the factory is set to 'False' (default).
    """

    def __init__(self, factory: FactoryType, required: bool = False, **kwargs: Any) -> None:
        # Skip SubFactory.__init__ to replace its factory wrapper with ours
        self.required = required
        super(SubFactory, self).__init__(**kwargs)
        self.factory_wrapper = CustomFactoryWrapper(factory)

    def __set_name__(self, owner: type[GenericDjangoModelFactory], name: str) -> None:
        self.owner = owner
        self.name = name

    @property
    def null(self) -> bool:
        if self.required:  # pragma: no cover
            return False
        return self.owner._meta.model._meta.get_field(self.name).null

    def evaluate(self, instance: Resolver, step: BuildStep, extra: dict[str, Any]) -> TModel | None:
        if not extra and self.null:
            return None
        return super().evaluate(instance, step, extra)


ForwardOneToOneFactory = ForeignKeyFactory
"""
Factory for forward 'one-to-one' related fields.
Basically the same as a SubFactory, but allows the related value to be 'None'.
"""


class ReverseOneToOneFactory(PostFactory[TModel]):
    """
    Factory for reverse 'one-to-one' related fields.
    If given the related model, or 'factory style arguments' (related__field=value),
    the related object is created and linked to the current instance.
    """

    def generate(self, instance: Model, create: bool, models: Iterable[TModel] | None, **kwargs: Any) -> None:
        if not models and kwargs:
            factory = self.get_factory()
            field_name = instance._meta.get_field(self.field_name).remote_field.name  # type: ignore
            kwargs.setdefault(field_name, instance)
            factory.create(**kwargs) if create else factory.build(**kwargs)


class ReverseForeignKeyFactory(PostFactory[TModel]):
    """
    Factory for reverse foreign keys (one-to-many).
    If given the related model, or "factory style arguments" (related__field=value),
    a single related object is created and linked to the current instance.
    """

    def generate(self, instance: Model, create: bool, models: Iterable[TModel] | None, **kwargs: Any) -> None:
        if not models and kwargs:
            factory = self.get_factory()
            manager = self.manager(instance)
            try:
                field_name = manager.field.name
            except AttributeError:  # pragma: no cover
                # GenericForeignKey
                field = next(
                    field
                    for field in manager.model._meta.get_fields()
                    if (
                        isinstance(field, GenericForeignKey)
                        and field.fk_field == manager.object_id_field_name
                        and field.ct_field == manager.content_type_field_name
                    )
                )
                field_name = field.name
            kwargs.setdefault(field_name, instance)
            factory.create(**kwargs) if create else factory.build(**kwargs)


class ManyToManyFactory(PostFactory[TModel]):
    """
    Factory for forward/reverse many-to-many related fields.
    If given the related model, or "factory style arguments" (related__field=value),
    a single related object is created and linked to the current instance.
    """

    def generate(self, instance: Model, create: bool, models: Iterable[TModel] | None, **kwargs: Any) -> None:
        if not models and kwargs:
            factory = self.get_factory()
            model = factory.create(**kwargs) if create else factory.build(**kwargs)
            self.manager(instance).add(model)

        for model in models or []:
            self.manager(instance).add(model)
