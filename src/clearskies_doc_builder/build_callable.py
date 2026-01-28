from typing import Any

from clearskies_doc_builder import models
from clearskies_doc_builder.prepare_doc_space import prepare_doc_space


def _infer_entry_type(entry: dict[str, Any]) -> str:
    """
    Infer the entry type from the builder class name.

    - Module builder -> "submodule" (contains multiple classes, acts as a section)
    - SingleClass builder -> "class" (documents a single class)
    - SingleClassToSection builder -> "class"
    - Other/unknown -> "" (will be sorted last)

    This can be overridden by explicitly setting "entry_type" in the config.
    """
    # Allow explicit override
    if "entry_type" in entry:
        return entry["entry_type"]

    builder = entry.get("builder", "")
    if builder.endswith(".Module"):
        return "submodule"
    elif builder.endswith(".SingleClass") or builder.endswith(".SingleClassToSection"):
        return "class"
    return ""


def _sort_key_for_entry(entry: dict[str, Any]) -> tuple[int, str]:
    """
    Generate a sort key for navigation ordering.

    Entries are sorted by:
    1. entry_type priority: "submodule" (0) comes before "class" (1) and others (2)
    2. title alphabetically (case-insensitive)

    This ensures submodules appear first in navigation, followed by classes,
    all sorted alphabetically within their group.

    Entry type is automatically inferred from the builder:
    - Module builder -> "submodule"
    - SingleClass/SingleClassToSection builder -> "class"
    """
    entry_type = _infer_entry_type(entry)
    type_priority = {"submodule": 0, "class": 1}.get(entry_type, 2)
    title = entry.get("title", "").lower()
    return (type_priority, title)


def _compute_nav_orders_and_child_counts(
    tree: list[dict[str, Any]],
) -> tuple[dict[int, int], dict[str, int]]:
    """
    Compute nav_order for each entry and count children per parent.

    Returns:
        - nav_orders: dict mapping original tree index to computed nav_order
        - child_counts: dict mapping parent title to number of child entries

    For entries with the same parent:
    - Groups by entry_type (submodules first, then classes)
    - Sorts alphabetically within each group
    - Assigns sequential nav_order values

    Top-level entries maintain their original order (index + 2).

    The child_counts is used by Module builders to offset their internal class
    nav_orders so that child entries (submodules) appear first in navigation.
    """
    # Group entries by their parent
    parent_groups: dict[str | None, list[tuple[int, dict[str, Any]]]] = {}

    for index, entry in enumerate(tree):
        parent = entry.get("parent")
        if parent not in parent_groups:
            parent_groups[parent] = []
        parent_groups[parent].append((index, entry))

    # Compute nav_order for each entry
    nav_orders: dict[int, int] = {}
    child_counts: dict[str, int] = {}

    for parent, entries in parent_groups.items():
        if parent is None:
            # Top-level entries: use original index-based ordering
            for original_index, entry in entries:
                nav_orders[original_index] = original_index + 2
        else:
            # Child entries: sort by type then alphabetically
            sorted_entries = sorted(entries, key=lambda x: _sort_key_for_entry(x[1]))
            for nav_order, (original_index, entry) in enumerate(sorted_entries, start=1):
                nav_orders[original_index] = nav_order

    # Count children for each parent (by title)
    for entry in tree:
        parent = entry.get("parent")
        if parent:
            child_counts[parent] = child_counts.get(parent, 0) + 1

    return nav_orders, child_counts


def build_callable(modules: models.Module, classes: models.Class, config: dict[str, Any], project_root: str):
    doc_root = prepare_doc_space(project_root)

    # Pre-compute nav_orders and child counts based on sorting rules
    nav_orders, child_counts = _compute_nav_orders_and_child_counts(config["tree"])

    for index, branch in enumerate(config["tree"]):
        nav_order = nav_orders[index]

        # Add child_entry_count to branch so Module builder can offset its class nav_orders
        # This ensures child entries (submodules) appear first in navigation
        branch_with_child_count = {
            **branch,
            "child_entry_count": child_counts.get(branch["title"], 0),
        }

        builder_class = classes.find("import_path=" + branch["builder"]).type
        builder = builder_class(
            branch_with_child_count,
            modules,
            classes,
            doc_root,
            nav_order=nav_order,
        )
        builder.build()
