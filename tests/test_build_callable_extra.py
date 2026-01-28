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
