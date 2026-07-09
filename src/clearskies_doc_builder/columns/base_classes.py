from __future__ import annotations

import clearskies


class BaseClasses(clearskies.columns.HasMany):
    def __init__(
        self,
        readable_child_column_names: list[str] = [],
    ):
        self.foreign_column_name = "type"
        self.readable_child_column_names = readable_child_column_names

    def finalize_configuration(self, model_class, name) -> None:
        self.child_model_class = model_class
        super().finalize_configuration(model_class, name)

    def __get__(self, instance, cls):
        if instance is None:
            self.model_class = cls
            return self

        # this makes sure we're initialized
        if not self._config or "name" not in self._config:
            instance.get_columns()

        bases = []
        for base_class in instance.type.__bases__:
            bases.append(instance.model(instance.backend.unpack(base_class, instance.module)))

        return bases
