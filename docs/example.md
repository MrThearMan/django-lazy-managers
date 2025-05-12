# Example

## Lazy managers

Given the following models:

```python
from django.db import models

class Project(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Task(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
```

We can delay the evaluation of a manager with the `LazyModelManager` descriptor:

```python
from typing import ClassVar, TYPE_CHECKING
from django.db import models
from lazy_managers import LazyModelManager

if TYPE_CHECKING:
    from .querysets import ProjectManager, TaskManager


class Project(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    objects: ClassVar[ProjectManager] = LazyModelManager.new()

class Task(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")

    objects: ClassVar[TaskManager] = LazyModelManager.new()
```

With this, our manager (and queryset) classes will be lazily loaded when it is first accessed,
either from the class itself, or from a to-many relationship.

The advantage of this is that our manager (and queryset) module can freely import other modules
without causing cyclical imports.

## Lazy attributes

The library also provides a way to lazily load other attributes on a model, with the
same benefits of avoiding cyclical imports.

```python
from typing import ClassVar, TYPE_CHECKING
from django.db import models
from lazy_managers import LazyModelAttribute

if TYPE_CHECKING:
    from .validators import ProjectValidators, TaskValidators


class Project(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    validators: ClassVar[ProjectValidators] = LazyModelAttribute.new()

class Task(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")

    validators: ClassVar[TaskValidators] = LazyModelAttribute.new()
```

Here the attribute should take a single argument, which is the instance of the model being accessed.
However, the attribute can be accessed on the class level, in which case the attribute class itself
will be given from the descriptor.
