from typing import Any

from clearskies_doc_builder import models
from clearskies_doc_builder.prepare_doc_space import prepare_doc_space


def build_callable(modules: models.Module, classes: models.Class, config: dict[str, Any], project_root: str):
    doc_root = prepare_doc_space(project_root)
    nav_order_parent_count: dict[str, int] = {}

    for index, branch in enumerate(config["tree"]):
        # For nav_order tracking, we need to track by the immediate parent
        # If there's a grand_parent, the parent is the immediate container
        # If there's only a parent, that's the immediate container
        # If neither, it's a top-level item (doesn't need tracking)
        parent = branch.get("parent")
        grand_parent = branch.get("grand_parent")

        # Determine nav_order based on hierarchy level
        if parent or grand_parent:
            # Child items: track by their immediate parent
            nav_order_title_tracker = parent
            if nav_order_title_tracker not in nav_order_parent_count:
                nav_order_parent_count[nav_order_title_tracker] = 0
            nav_order_parent_count[nav_order_title_tracker] += 1
            nav_order = nav_order_parent_count[nav_order_title_tracker]
        else:
            # Top-level items: use index-based nav_order
            nav_order = index + 2

        builder_class = classes.find("import_path=" + branch["builder"]).type
        builder = builder_class(
            branch,
            modules,
            classes,
            doc_root,
            nav_order=nav_order,
        )
        builder.build()
