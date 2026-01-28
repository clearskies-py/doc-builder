import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))
import pytest

import clearskies_doc_builder.prepare_doc_space


@pytest.fixture(autouse=True)
def patch_prepare_doc_space(monkeypatch):
    import clearskies_doc_builder
    import clearskies_doc_builder.prepare_doc_space

    clearskies_doc_builder.prepare_doc_space.prepare_doc_space = lambda project_root: "/tmp/build"


import clearskies_doc_builder.build_callable
import clearskies_doc_builder.prepare_doc_space
from clearskies_doc_builder import models
from clearskies_doc_builder.build_callable import build_callable

prepare_doc_space_orig = None
if hasattr(build_callable, "__globals__"):
    prepare_doc_space_orig = build_callable.__globals__["prepare_doc_space"]
    build_callable.__globals__["prepare_doc_space"] = lambda project_root: "/tmp/build"


def test_build_callable_runs(monkeypatch):
    # Setup dummy config and objects
    class DummyModule:
        pass

    class DummyClass:
        def find(self, query):
            class DummyType:
                type = DummyBuilder

            return DummyType()

    class DummyBuilder:
        def __init__(self, branch, modules, classes, doc_root, nav_order):
            pass

        def build(self):
            DummyBuilder.called = True

    DummyBuilder.called = False

    config = {"tree": [{"title": "Test", "source": "", "builder": "dummy.path", "parent": None}]}
    project_root = "/tmp"
    modules = DummyModule()
    classes = DummyClass()

    build_callable(modules, classes, config, project_root)
    assert DummyBuilder.called
