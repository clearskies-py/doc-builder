from __future__ import annotations

import clearskies


class ModuleClasses(clearskies.columns.HasMany):
    def __init__(
        self,
        child_model_class,
        readable_child_column_names: list[str] = [],
    ):
        super().__init__(
            child_model_class,
            foreign_column_name="module",
            readable_child_column_names=readable_child_column_names,
        )

    def __get__(self, instance, cls):
        if instance is None:
            self.model_class = cls
            return self

        # this makes sure we're initialized
        if not self._config or "name" not in self._config:
            instance.get_columns()

        return self.child_model.where(cls.module.equals(instance.module))
