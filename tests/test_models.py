import pytest

from clearskies_doc_builder.models.attribute import Attribute
from clearskies_doc_builder.models.class_model import Class
from clearskies_doc_builder.models.module import Module


def test_attribute_fields():
    # Only check for class attributes, not instance attributes
    for field in ["id", "name", "type", "doc", "attribute", "parent_class"]:
        assert hasattr(Attribute, field)


def test_class_fields():
    for field in [
        "id",
        "type",
        "source_file",
        "import_path",
        "name",
        "doc",
        "module",
        "base_classes",
        "attributes",
        "methods",
        "init",
    ]:
        assert hasattr(Class, field)


def test_module_fields():
    for field in ["id", "import_path", "source_file", "is_builtin", "name", "doc", "module", "classes"]:
        assert hasattr(Module, field)
