# docs

The documentation builder for clearskies and related plugins

## Overview

Each "official" clearskies module (including the core clearskies library itself) has the documentation primarily written in the codebase as docblocks.  The documentation site is then built by extracting these docblocks and stitching them together.  To be clear, this isn't about the low-level "API" documentation that describes every single class/method in the framework.  Rather, this is about the primary documentation site itself (clearskies.info) which is focused on high-level use cases and examples of the primary configuration options.  As a result, it's not a simple matter of just iterating over the classes/methods and building documentation.  To build a coherent documentation site, each plugin has a configuration file that basically outlines the final "structure" or organization of the resulting documentation, as well as the name of a builder class that will combine that configuration information with the codebase itself to create the actual docs.

The docs themselves (in the source code) are all written with markdown.  This documentation builder then takes that markdwon and adds the necessary headers/etc so to make them valid files for [Jekyll](https://jekyllrb.com/), the builder for the current documentation site.  The site itself is hosted in S3, so building an actual documentation site means:

 1. Properly documenting everything inside of the source code via markdown.
 2. Creating a config file (`docs/python/config.json`) to map source code docs to Jekyll files.
 3. Creating a skeleton of a Jekyll site in the `doc/jekyll` folder of the plugin.
 4. Installing this doc builder via `poetry add clear-skies-doc-builder`.
 5. Run the doc builder.
 6. Build with Jekyll.
 7. Push to the appropriate subfolder via S3.
 8. (Only once) Update the main clearskies doc site to know about the new subfolder for this plugin.

Of course, we want the Jekyll sites to be consistent with eachother in terms of style/look.  In the long run we'll probably have this doc builder also bootstrap the Jekyll site, but for now you just have to manually setup the Jekyll build using the main clearskies repo as a template.

## Configuration File Structure

The `config.json` file defines the documentation structure using a tree of entries. Each entry specifies a documentation section with its source class and builder.

### Basic Structure

```json
{
  "tree": [
    {
      "title": "Section Title",
      "source": "package.module.ClassName",
      "builder": "clearskies_doc_builder.builders.Module",
      "classes": ["package.module.Class1", "package.module.Class2"]
    }
  ]
}
```

### Nested Hierarchy (Parent/Grand-Parent)

The doc builder supports up to 3 levels of navigation hierarchy using `parent` and `grand_parent` fields. This is useful for organizing documentation of submodules under a common heading.

#### Two-Level Hierarchy (Parent) - Module with Classes

Use this when you want to document a submodule's classes under a parent section:

```json
{
  "tree": [
    {
      "title": "Cursors",
      "source": "clearskies.cursors.Cursor",
      "builder": "clearskies_doc_builder.builders.Module",
      "classes": [
        "clearskies.cursors.MemoryCursor",
        "clearskies.cursors.FileCursor"
      ]
    },
    {
      "title": "From Environment",
      "source": "clearskies.cursors.from_environment.FromEnvironmentBase",
      "builder": "clearskies_doc_builder.builders.Module",
      "parent": "Cursors",
      "classes": [
        "clearskies.cursors.from_environment.EnvCursor",
        "clearskies.cursors.from_environment.SecretsCursor"
      ]
    }
  ]
}
```

This creates:
- `docs/cursors/index.md` - Parent section with overview
- `docs/cursors/memory-cursor.md` - Class documentation
- `docs/cursors/file-cursor.md` - Class documentation
- `docs/cursors/from-environment/index.md` - Submodule section with `parent: Cursors`
- `docs/cursors/from-environment/env-cursor.md` - Class with `parent: From Environment`
- `docs/cursors/from-environment/secrets-cursor.md` - Class with `parent: From Environment`

#### Three-Level Hierarchy (Grand-Parent)

For deeper nesting, use `grand_parent` to create a third level:

```json
{
  "tree": [
    {
      "title": "Cursors",
      "source": "clearskies.cursors.Cursor",
      "builder": "clearskies_doc_builder.builders.Module",
      "classes": ["clearskies.cursors.MemoryCursor"]
    },
    {
      "title": "From Environment",
      "source": "clearskies.cursors.from_environment.FromEnvironmentBase",
      "builder": "clearskies_doc_builder.builders.SingleClass",
      "parent": "Cursors"
    },
    {
      "title": "AWS Secrets",
      "source": "clearskies.cursors.from_environment.aws.AWSSecretsBase",
      "builder": "clearskies_doc_builder.builders.Module",
      "parent": "From Environment",
      "grand_parent": "Cursors",
      "classes": [
        "clearskies.cursors.from_environment.aws.SecretsManagerCursor",
        "clearskies.cursors.from_environment.aws.ParameterStoreCursor"
      ]
    }
  ]
}
```

This creates:
- `docs/cursors/index.md` - Grand-parent section
- `docs/cursors/from-environment/index.md` - Parent section with `parent: Cursors`
- `docs/cursors/from-environment/aws-secrets/index.md` - Child section with `parent: From Environment` and `grand_parent: Cursors`
- `docs/cursors/from-environment/aws-secrets/secrets-manager-cursor.md` - Class documentation

The `grand_parent` field enables the Jekyll "just-the-docs" theme's three-level navigation, allowing you to document submodule classes under their logical grouping.

#### Using SingleClass for Individual Classes

You can also use `SingleClass` builder for documenting individual classes within a hierarchy:

```json
{
  "tree": [
    {
      "title": "Cursors",
      "source": "clearskies.cursors.Cursor",
      "builder": "clearskies_doc_builder.builders.SingleClass"
    },
    {
      "title": "Environment Cursor",
      "source": "clearskies.cursors.from_environment.EnvironmentCursor",
      "builder": "clearskies_doc_builder.builders.SingleClass",
      "parent": "Cursors"
    }
  ]
}
```
