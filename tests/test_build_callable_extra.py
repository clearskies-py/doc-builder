import pytest

from clearskies_doc_builder.build_callable import build_callable


class DummyModule:
    pass


class DummyBuilder:
    init_args: tuple | None = None
    build_called: bool = False

    def __init__(self, branch, modules, classes, doc_root, nav_order):
        DummyBuilder.init_args = (branch, modules, classes, doc_root, nav_order)

    def build(self):
        DummyBuilder.build_called = True


class DummyClass:
    def __init__(self, builders):
        self.builders = builders
        self.find_calls = []

    def find(self, query):
        self.find_calls.append(query)

        class DummyType:
            type = self.builders.pop(0)

        return DummyType()


def test_build_callable_multiple_branches(monkeypatch):
    import clearskies_doc_builder.prepare_doc_space

    clearskies_doc_builder.prepare_doc_space.prepare_doc_space = lambda project_root: "/tmp/build"
    import clearskies_doc_builder.build_callable

    clearskies_doc_builder.build_callable.__globals__["prepare_doc_space"] = (
        clearskies_doc_builder.prepare_doc_space.prepare_doc_space
    )
    config = {
        "tree": [
            {"title": "A", "source": "", "builder": "dummy.path.A", "parent": None},
            {"title": "B", "source": "", "builder": "dummy.path.B", "parent": "A"},
        ]
    }
    modules = DummyModule()
    classes = DummyClass([DummyBuilder, DummyBuilder])
    build_callable(modules, classes, config, "/tmp")
    assert classes.find_calls == ["import_path=dummy.path.A", "import_path=dummy.path.B"]
    assert DummyBuilder.build_called
    assert DummyBuilder.init_args[0]["title"] == "B"


def test_build_callable_nav_order(monkeypatch):
    import clearskies_doc_builder.prepare_doc_space

    clearskies_doc_builder.prepare_doc_space.prepare_doc_space = lambda project_root: "/tmp/build"
    import clearskies_doc_builder.build_callable

    clearskies_doc_builder.build_callable.__globals__["prepare_doc_space"] = (
        clearskies_doc_builder.prepare_doc_space.prepare_doc_space
    )
    config = {
        "tree": [
            {"title": "Parent", "source": "", "builder": "dummy.path.Parent", "parent": None},
            {"title": "Child", "source": "", "builder": "dummy.path.Child", "parent": "Parent"},
        ]
    }
    modules = DummyModule()
    classes = DummyClass([DummyBuilder, DummyBuilder])
    build_callable(modules, classes, config, "/tmp")
    # Child nav_order should be nav_order_parent_count[Parent]
    assert DummyBuilder.init_args[4] == 1 or DummyBuilder.init_args[4] == 2


def test_build_callable_grand_parent(monkeypatch):
    """Test three-level hierarchy with grand_parent support."""
    import clearskies_doc_builder.prepare_doc_space

    clearskies_doc_builder.prepare_doc_space.prepare_doc_space = lambda project_root: "/tmp/build"
    import clearskies_doc_builder.build_callable

    clearskies_doc_builder.build_callable.__globals__["prepare_doc_space"] = (
        clearskies_doc_builder.prepare_doc_space.prepare_doc_space
    )

    # Track all builder init calls
    all_init_args = []

    class TrackingBuilder:
        def __init__(self, branch, modules, classes, doc_root, nav_order):
            all_init_args.append((branch, modules, classes, doc_root, nav_order))

        def build(self):
            pass

    config = {
        "tree": [
            {"title": "Cursors", "source": "", "builder": "dummy.path.Cursors"},
            {"title": "From Environment", "source": "", "builder": "dummy.path.FromEnv", "parent": "Cursors"},
            {
                "title": "EnvCursor",
                "source": "",
                "builder": "dummy.path.EnvCursor",
                "parent": "From Environment",
                "grand_parent": "Cursors",
            },
        ]
    }
    modules = DummyModule()
    classes = DummyClass([TrackingBuilder, TrackingBuilder, TrackingBuilder])
    build_callable(modules, classes, config, "/tmp")

    # Verify all three builders were called
    assert len(all_init_args) == 3

    # First item (Cursors) should be top-level with nav_order = 2 (index + 2)
    assert all_init_args[0][0]["title"] == "Cursors"
    assert all_init_args[0][4] == 2  # nav_order

    # Second item (From Environment) should have parent = Cursors, nav_order = 1
    assert all_init_args[1][0]["title"] == "From Environment"
    assert all_init_args[1][0]["parent"] == "Cursors"
    assert all_init_args[1][4] == 1  # nav_order (first child of Cursors)

    # Third item (EnvCursor) should have parent = From Environment, grand_parent = Cursors
    assert all_init_args[2][0]["title"] == "EnvCursor"
    assert all_init_args[2][0]["parent"] == "From Environment"
    assert all_init_args[2][0]["grand_parent"] == "Cursors"
    assert all_init_args[2][4] == 1  # nav_order (first child of From Environment)


def test_build_callable_multiple_grandchildren(monkeypatch):
    """Test multiple grandchildren under the same parent."""
    import clearskies_doc_builder.prepare_doc_space

    clearskies_doc_builder.prepare_doc_space.prepare_doc_space = lambda project_root: "/tmp/build"
    import clearskies_doc_builder.build_callable

    clearskies_doc_builder.build_callable.__globals__["prepare_doc_space"] = (
        clearskies_doc_builder.prepare_doc_space.prepare_doc_space
    )

    all_init_args = []

    class TrackingBuilder:
        def __init__(self, branch, modules, classes, doc_root, nav_order):
            all_init_args.append((branch, modules, classes, doc_root, nav_order))

        def build(self):
            pass

    config = {
        "tree": [
            {"title": "Cursors", "source": "", "builder": "dummy.path.Cursors"},
            {"title": "From Environment", "source": "", "builder": "dummy.path.FromEnv", "parent": "Cursors"},
            {
                "title": "EnvCursor1",
                "source": "",
                "builder": "dummy.path.EnvCursor1",
                "parent": "From Environment",
                "grand_parent": "Cursors",
            },
            {
                "title": "EnvCursor2",
                "source": "",
                "builder": "dummy.path.EnvCursor2",
                "parent": "From Environment",
                "grand_parent": "Cursors",
            },
        ]
    }
    modules = DummyModule()
    classes = DummyClass([TrackingBuilder, TrackingBuilder, TrackingBuilder, TrackingBuilder])
    build_callable(modules, classes, config, "/tmp")

    # Verify all four builders were called
    assert len(all_init_args) == 4

    # EnvCursor1 should have nav_order = 1 (first child of From Environment)
    assert all_init_args[2][0]["title"] == "EnvCursor1"
    assert all_init_args[2][4] == 1

    # EnvCursor2 should have nav_order = 2 (second child of From Environment)
    assert all_init_args[3][0]["title"] == "EnvCursor2"
    assert all_init_args[3][4] == 2


def test_build_callable_module_without_classes(monkeypatch):
    """Test Module builder can be used as parent-only section without classes."""
    import clearskies_doc_builder.prepare_doc_space

    clearskies_doc_builder.prepare_doc_space.prepare_doc_space = lambda project_root: "/tmp/build"
    import clearskies_doc_builder.build_callable

    clearskies_doc_builder.build_callable.__globals__["prepare_doc_space"] = (
        clearskies_doc_builder.prepare_doc_space.prepare_doc_space
    )

    all_init_args = []

    class TrackingBuilder:
        def __init__(self, branch, modules, classes, doc_root, nav_order):
            all_init_args.append((branch, modules, classes, doc_root, nav_order))

        def build(self):
            pass

    # Config with a parent section that has no classes (just acts as navigation parent)
    config = {
        "tree": [
            {
                "title": "Cursors",
                "source": "clearskies.cursors.Cursor",
                "builder": "clearskies_doc_builder.builders.Module",
                # No "classes" field - this is a parent-only section
            },
            {
                "title": "IAM Cursors",
                "source": "clearskies.cursors.iam.IamCursor",
                "builder": "clearskies_doc_builder.builders.Module",
                "parent": "Cursors",
                "classes": ["clearskies.cursors.iam.RdsMysql"],
            },
        ]
    }
    modules = DummyModule()
    classes = DummyClass([TrackingBuilder, TrackingBuilder])
    build_callable(modules, classes, config, "/tmp")

    # Verify both builders were called
    assert len(all_init_args) == 2

    # First item (Cursors) should be top-level with no classes
    assert all_init_args[0][0]["title"] == "Cursors"
    assert "classes" not in all_init_args[0][0] or all_init_args[0][0].get("classes") is None

    # Second item (IAM Cursors) should have parent = Cursors
    assert all_init_args[1][0]["title"] == "IAM Cursors"
    assert all_init_args[1][0]["parent"] == "Cursors"
    assert all_init_args[1][0]["classes"] == ["clearskies.cursors.iam.RdsMysql"]


def test_build_callable_entry_type_sorting(monkeypatch):
    """Test that entries are sorted by entry_type (submodules first) then alphabetically."""
    import clearskies_doc_builder.prepare_doc_space

    clearskies_doc_builder.prepare_doc_space.prepare_doc_space = lambda project_root: "/tmp/build"
    import clearskies_doc_builder.build_callable

    clearskies_doc_builder.build_callable.__globals__["prepare_doc_space"] = (
        clearskies_doc_builder.prepare_doc_space.prepare_doc_space
    )

    all_init_args = []

    class TrackingBuilder:
        def __init__(self, branch, modules, classes, doc_root, nav_order):
            all_init_args.append((branch, modules, classes, doc_root, nav_order))

        def build(self):
            pass

    # Config with mixed entry_types under the same parent
    # Classes: Zebra, Apple
    # Submodules: Mango, Banana
    # Expected order: Banana (submodule), Mango (submodule), Apple (class), Zebra (class)
    config = {
        "tree": [
            {"title": "Cursors", "source": "", "builder": "dummy.path.Cursors"},
            {
                "title": "Zebra",
                "source": "",
                "builder": "dummy.path.Zebra",
                "parent": "Cursors",
                "entry_type": "class",
            },
            {
                "title": "Apple",
                "source": "",
                "builder": "dummy.path.Apple",
                "parent": "Cursors",
                "entry_type": "class",
            },
            {
                "title": "Mango",
                "source": "",
                "builder": "dummy.path.Mango",
                "parent": "Cursors",
                "entry_type": "submodule",
            },
            {
                "title": "Banana",
                "source": "",
                "builder": "dummy.path.Banana",
                "parent": "Cursors",
                "entry_type": "submodule",
            },
        ]
    }
    modules = DummyModule()
    classes = DummyClass([TrackingBuilder] * 5)
    build_callable(modules, classes, config, "/tmp")

    # Verify all five builders were called
    assert len(all_init_args) == 5

    # Get nav_orders for each child entry (skip the parent at index 0)
    child_nav_orders = {all_init_args[i][0]["title"]: all_init_args[i][4] for i in range(1, 5)}

    # Submodules should come first (alphabetically): Banana=1, Mango=2
    # Classes should come after (alphabetically): Apple=3, Zebra=4
    assert child_nav_orders["Banana"] == 1, f"Banana should be 1, got {child_nav_orders['Banana']}"
    assert child_nav_orders["Mango"] == 2, f"Mango should be 2, got {child_nav_orders['Mango']}"
    assert child_nav_orders["Apple"] == 3, f"Apple should be 3, got {child_nav_orders['Apple']}"
    assert child_nav_orders["Zebra"] == 4, f"Zebra should be 4, got {child_nav_orders['Zebra']}"


def test_build_callable_entry_type_sorting_without_type(monkeypatch):
    """Test that entries without entry_type are sorted after submodules and classes."""
    import clearskies_doc_builder.prepare_doc_space

    clearskies_doc_builder.prepare_doc_space.prepare_doc_space = lambda project_root: "/tmp/build"
    import clearskies_doc_builder.build_callable

    clearskies_doc_builder.build_callable.__globals__["prepare_doc_space"] = (
        clearskies_doc_builder.prepare_doc_space.prepare_doc_space
    )

    all_init_args = []

    class TrackingBuilder:
        def __init__(self, branch, modules, classes, doc_root, nav_order):
            all_init_args.append((branch, modules, classes, doc_root, nav_order))

        def build(self):
            pass

    # Config with mixed entry_types including entries without type
    config = {
        "tree": [
            {"title": "Cursors", "source": "", "builder": "dummy.path.Cursors"},
            {
                "title": "NoType",
                "source": "",
                "builder": "dummy.path.NoType",
                "parent": "Cursors",
                # No entry_type
            },
            {
                "title": "MyClass",
                "source": "",
                "builder": "dummy.path.MyClass",
                "parent": "Cursors",
                "entry_type": "class",
            },
            {
                "title": "MySubmodule",
                "source": "",
                "builder": "dummy.path.MySubmodule",
                "parent": "Cursors",
                "entry_type": "submodule",
            },
        ]
    }
    modules = DummyModule()
    classes = DummyClass([TrackingBuilder] * 4)
    build_callable(modules, classes, config, "/tmp")

    # Get nav_orders for each child entry
    child_nav_orders = {all_init_args[i][0]["title"]: all_init_args[i][4] for i in range(1, 4)}

    # Order: MySubmodule (submodule=1), MyClass (class=2), NoType (other=3)
    assert child_nav_orders["MySubmodule"] == 1
    assert child_nav_orders["MyClass"] == 2
    assert child_nav_orders["NoType"] == 3


def test_build_callable_auto_infer_entry_type(monkeypatch):
    """Test that entry_type is automatically inferred from builder name."""
    import clearskies_doc_builder.prepare_doc_space

    clearskies_doc_builder.prepare_doc_space.prepare_doc_space = lambda project_root: "/tmp/build"
    import clearskies_doc_builder.build_callable

    clearskies_doc_builder.build_callable.__globals__["prepare_doc_space"] = (
        clearskies_doc_builder.prepare_doc_space.prepare_doc_space
    )

    all_init_args = []

    class TrackingBuilder:
        def __init__(self, branch, modules, classes, doc_root, nav_order):
            all_init_args.append((branch, modules, classes, doc_root, nav_order))

        def build(self):
            pass

    # Config using actual builder names that will be auto-detected
    # Module -> submodule, SingleClass -> class
    config = {
        "tree": [
            {"title": "Cursors", "source": "", "builder": "clearskies_doc_builder.builders.Module"},
            {
                "title": "Zebra Class",
                "source": "",
                "builder": "clearskies_doc_builder.builders.SingleClass",  # Auto-detected as "class"
                "parent": "Cursors",
            },
            {
                "title": "Apple Class",
                "source": "",
                "builder": "clearskies_doc_builder.builders.SingleClass",  # Auto-detected as "class"
                "parent": "Cursors",
            },
            {
                "title": "Mango Submodule",
                "source": "",
                "builder": "clearskies_doc_builder.builders.Module",  # Auto-detected as "submodule"
                "parent": "Cursors",
            },
            {
                "title": "Banana Submodule",
                "source": "",
                "builder": "clearskies_doc_builder.builders.Module",  # Auto-detected as "submodule"
                "parent": "Cursors",
            },
        ]
    }
    modules = DummyModule()
    classes = DummyClass([TrackingBuilder] * 5)
    build_callable(modules, classes, config, "/tmp")

    # Verify all five builders were called
    assert len(all_init_args) == 5

    # Get nav_orders for each child entry (skip the parent at index 0)
    child_nav_orders = {all_init_args[i][0]["title"]: all_init_args[i][4] for i in range(1, 5)}

    # Submodules (Module builder) should come first (alphabetically): Banana=1, Mango=2
    # Classes (SingleClass builder) should come after (alphabetically): Apple=3, Zebra=4
    assert child_nav_orders["Banana Submodule"] == 1, f"Expected 1, got {child_nav_orders['Banana Submodule']}"
    assert child_nav_orders["Mango Submodule"] == 2, f"Expected 2, got {child_nav_orders['Mango Submodule']}"
    assert child_nav_orders["Apple Class"] == 3, f"Expected 3, got {child_nav_orders['Apple Class']}"
    assert child_nav_orders["Zebra Class"] == 4, f"Expected 4, got {child_nav_orders['Zebra Class']}"


def test_build_callable_child_entry_count(monkeypatch):
    """Test that child_entry_count is passed to builders for nav_order offset."""
    import clearskies_doc_builder.prepare_doc_space

    clearskies_doc_builder.prepare_doc_space.prepare_doc_space = lambda project_root: "/tmp/build"
    import clearskies_doc_builder.build_callable

    clearskies_doc_builder.build_callable.__globals__["prepare_doc_space"] = (
        clearskies_doc_builder.prepare_doc_space.prepare_doc_space
    )

    all_init_args = []

    class TrackingBuilder:
        def __init__(self, branch, modules, classes, doc_root, nav_order):
            all_init_args.append((branch, modules, classes, doc_root, nav_order))

        def build(self):
            pass

    # Config simulating the Cursors scenario:
    # - Cursors (parent with classes)
    # - From Environment (child submodule)
    # - Port Forwarders (child submodule)
    config = {
        "tree": [
            {
                "title": "Cursors",
                "source": "clearskies.cursors.Cursor",
                "builder": "clearskies_doc_builder.builders.Module",
                "classes": ["clearskies.cursors.Sqlite", "clearskies.cursors.Mysql"],
            },
            {
                "title": "From Environment",
                "source": "clearskies.cursors.from_environment.Base",
                "builder": "clearskies_doc_builder.builders.Module",
                "parent": "Cursors",
                "classes": ["clearskies.cursors.from_environment.Sqlite"],
            },
            {
                "title": "Port Forwarders",
                "source": "clearskies.cursors.port_forwarding.Base",
                "builder": "clearskies_doc_builder.builders.Module",
                "parent": "Cursors",
                "classes": ["clearskies.cursors.port_forwarding.Ssh"],
            },
        ]
    }
    modules = DummyModule()
    classes = DummyClass([TrackingBuilder] * 3)
    build_callable(modules, classes, config, "/tmp")

    # Verify all three builders were called
    assert len(all_init_args) == 3

    # Cursors should have child_entry_count = 2 (From Environment + Port Forwarders)
    cursors_branch = all_init_args[0][0]
    assert cursors_branch["title"] == "Cursors"
    assert cursors_branch["child_entry_count"] == 2

    # From Environment should have child_entry_count = 0 (no children)
    from_env_branch = all_init_args[1][0]
    assert from_env_branch["title"] == "From Environment"
    assert from_env_branch["child_entry_count"] == 0

    # Port Forwarders should have child_entry_count = 0 (no children)
    port_fwd_branch = all_init_args[2][0]
    assert port_fwd_branch["title"] == "Port Forwarders"
    assert port_fwd_branch["child_entry_count"] == 0
