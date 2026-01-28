from collections import OrderedDict
from typing import Any

import clearskies

from .builder import Builder


class Module(Builder):
    def __init__(self, branch, modules, classes, doc_root, nav_order):
        super().__init__(branch, modules, classes, doc_root, nav_order)
        self.class_list = branch["classes"]
        self.args_to_additional_attributes_map = branch.get("args_to_additional_attributes_map", {})
        self.parent = branch.get("parent", False)
        self.grand_parent = branch.get("grand_parent", False)

    def build(self):
        title_snake_case = clearskies.functional.string.title_case_to_snake_case(self.title.replace(" ", "")).replace(
            "_", "-"
        )

        # Determine the section folder path based on hierarchy
        if self.grand_parent:
            # Three-level hierarchy: grand_parent/parent/title/
            grand_parent_snake = (
                clearskies.functional.string.title_case_to_snake_case(self.grand_parent)
                .replace("_", "-")
                .replace(" ", "")
            )
            parent_snake = (
                clearskies.functional.string.title_case_to_snake_case(self.parent).replace("_", "-").replace(" ", "")
            )
            section_name = f"{grand_parent_snake}/{parent_snake}/{title_snake_case}"
            section_folder_path = self.doc_root / grand_parent_snake / parent_snake / title_snake_case
        elif self.parent:
            # Two-level hierarchy: parent/title/
            parent_snake = (
                clearskies.functional.string.title_case_to_snake_case(self.parent).replace("_", "-").replace(" ", "")
            )
            section_name = f"{parent_snake}/{title_snake_case}"
            section_folder_path = self.doc_root / parent_snake / title_snake_case
        else:
            # Top-level: title/
            section_name = title_snake_case
            section_folder_path = self.doc_root / title_snake_case

        source_class = self.classes.find(f"import_path={self.source}")
        self.make_index_from_class_overview_with_hierarchy(
            title_snake_case, source_class, section_folder_path, section_name
        )

        default_args = self.default_args()

        nav_order = 0
        for class_name in self.class_list:
            nav_order += 1
            source_class = self.classes.find(f"import_path={class_name}")
            title = source_class.name
            filename = clearskies.functional.string.title_case_to_snake_case(source_class.name).replace("_", "-")
            # For classes within a module, the module title becomes the parent
            # and if the module has a parent, that becomes the grand_parent
            class_grand_parent = self.parent if self.parent else None
            class_doc = self.build_header(
                source_class.name, filename, section_name, self.title, nav_order, False, class_grand_parent
            )
            (elevator_pitch, overview) = self.parse_overview_doc(
                self.raw_docblock_to_md(source_class.doc).lstrip("\n").lstrip(" ")
            )
            class_doc += f"\n\n# {title}\n\n{elevator_pitch}\n\n"
            main_doc = f"## Overview\n\n{overview}\n\n"
            table_of_contents = " 1. [Overview](#overview)\n"

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
            docs = self.extract_attribute_docs(source_class, list(arguments.keys()))
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

            output_file = section_folder_path / f"{filename}.md"
            with output_file.open(mode="w") as doc_file:
                doc_file.write(class_doc)
