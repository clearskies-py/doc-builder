from __future__ import annotations

from typing import Callable

import clearskies


class Attribute(clearskies.columns.HasMany):
    def __init__(
        self,
        child_model_class,
        readable_child_column_names: list[str] = [],
        filter: Callable | None = None,
    ):
        self.filter = filter
        super().__init__(
            child_model_class,
            foreign_column_name="parent_class",
            readable_child_column_names=readable_child_column_names,
        )

    def __get__(self, instance, cls):
        if instance is None:
            self.model_class = cls
            return self

        # this makes sure we're initialized
        if not self._config or "name" not in self._config:
            instance.get_columns()

        parent_class_column = getattr(self.child_model_class, "parent_class")
        attributes = self.child_model.where(parent_class_column.equals(instance.type))
        if self.filter:
            filtered_attributes = list(filter(self.filter, attributes))
            return filtered_attributes[0]

        all_attributes = list(attributes)
        return all_attributes[0]
