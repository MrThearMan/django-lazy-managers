from __future__ import annotations

from django.apps import AppConfig

__all__ = [
    "ExampleConfig",
]


class ExampleConfig(AppConfig):
    name = "example_project.app"
    verbose_name = "Example"
    default_auto_field = "django.db.models.BigAutoField"
