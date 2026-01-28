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
