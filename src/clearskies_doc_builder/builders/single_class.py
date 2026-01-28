from collections import OrderedDict
from typing import Any

import clearskies

from .builder import Builder


class SingleClass(Builder):
    def __init__(self, branch, modules, classes, doc_root, nav_order):
        super().__init__(branch, modules, classes, doc_root, nav_order)
        self.additional_attribute_sources = branch.get("additional_attribute_sources", [])
        self.args_to_additional_attributes_map = branch.get("args_to_additional_attributes_map", {})
        self.parent = branch.get("parent", False)
        self.grand_parent = branch.get("grand_parent", False)

    def build(self):
        # Determine the section folder path based on hierarchy
        if self.grand_parent:
            # Three-level hierarchy: grand_parent/parent/file.md
            grand_parent_snake = (
                clearskies.functional.string.title_case_to_snake_case(self.grand_parent)
                .replace("_", "-")
                .replace(" ", "")
            )
            parent_snake = (
                clearskies.functional.string.title_case_to_snake_case(self.parent).replace("_", "-").replace(" ", "")
            )
            section_name = f"{grand_parent_snake}/{parent_snake}"
            section_folder_path = self.doc_root / grand_parent_snake / parent_snake
        elif self.parent:
            # Two-level hierarchy: parent/file.md
            section_name = (
                clearskies.functional.string.title_case_to_snake_case(self.parent).replace("_", "-").replace(" ", "")
            )
            section_folder_path = self.doc_root / section_name
        else:
            # Top-level: title/index.md
            section_name = (
                clearskies.functional.string.title_case_to_snake_case(self.title).replace("_", "-").replace(" ", "")
            )
            section_folder_path = self.doc_root / section_name

        section_folder_path.mkdir(parents=True, exist_ok=True)
        source_class = self.classes.find(f"import_path={self.source}")

        title_snake_case = clearskies.functional.string.title_case_to_snake_case(self.title.replace(" ", "")).replace(
            "_", "-"
        )
        class_doc = self.build_header(
            self.title, title_snake_case, section_name, self.parent, self.nav_order, False, self.grand_parent
        )
        (elevator_pitch, overview) = self.parse_overview_doc(
            self.raw_docblock_to_md(source_class.doc).lstrip("\n").lstrip(" ")
        )
        class_doc += f"\n\n# {self.title}\n\n{elevator_pitch}\n\n"
        main_doc = f"## Overview\n\n{overview}\n\n"
        table_of_contents = " 1. [Overview](#overview)\n"

        default_args = self.default_args()

        # Find the documentation for all of our init args.
        arguments: dict[str, Any] = OrderedDict()
        for arg in source_class.init.all_args:
            if arg == "self":
                continue
            arguments[arg] = {
                "required": arg not in source_class.init.kwargs,
                "doc": default_args.get(arg, ""),
            }

        # for various reasons, it's easier to extract docs for all the arguments at once:
        docs = self.extract_attribute_docs(
            source_class,
            list(arguments.keys()),
            additional_attribute_sources=[
                self.classes.find(f"import_path={source}") for source in self.additional_attribute_sources
            ],
        )
        for arg, doc in docs.items():
            # you would think that we would only get arguments that belong to our class, but this isn't the case
            # because the processing caches results from parent classes, and we don't always use all attributes
            # available from all our parents.
            if arg not in arguments:
                continue
            arguments[arg]["doc"] = doc

        for index, arg in enumerate(arguments.keys()):
            arg_data = arguments[arg]
            table_of_contents += f" {index + 2}. [{arg}](#{arg})\n"
            main_doc += f"## {arg}\n**" + ("Required" if arg_data["required"] else "Optional") + "**\n\n"
            main_doc += self.raw_docblock_to_md(arg_data["doc"].replace('"""', "")) + "\n\n"

        class_doc += f"{table_of_contents}\n{main_doc}"

        # Determine output filename based on hierarchy level
        if self.parent or self.grand_parent:
            # Child or grandchild: use title as filename
            output_filename = (
                clearskies.functional.string.title_case_to_snake_case(self.title.replace(" ", "")).replace("_", "-")
                + ".md"
            )
        else:
            # Top-level: use index.md
            output_filename = "index.md"

        output_file = section_folder_path / output_filename
        with output_file.open(mode="w") as doc_file:
            doc_file.write(class_doc)
