import pathlib
import shutil


def prepare_doc_space(project_root):
    project_path = pathlib.Path(project_root)
    build_path = project_path / "build"
    doc_path = build_path / "docs"
    jekyll_path = project_path / "jekyll"
    includes_path = jekyll_path / "_includes"

    if doc_path.is_dir():
        shutil.rmtree(doc_path)
    build_path.mkdir(parents=True, exist_ok=True)

    for file in jekyll_path.glob("*"):
        if not file.is_file():
            continue
        shutil.copy2(str(file), str(build_path / file.name))

    shutil.copytree(str(jekyll_path / "docs"), str(build_path / "docs"))
    if includes_path.is_dir():
        shutil.copytree(str(includes_path), str(build_path / "_includes"))

    return str(doc_path)
