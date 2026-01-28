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

#### Parent-Only Sections (No Classes)

You can create a parent section that only serves as a navigation container without documenting any classes directly. This is useful when you want to group multiple submodules under a common heading:

```json
{
  "tree": [
    {
      "title": "Cursors",
      "source": "clearskies.cursors.Cursor",
      "builder": "clearskies_doc_builder.builders.Module"
    },
    {
      "title": "IAM Cursors",
      "source": "clearskies.cursors.iam.IamCursor",
      "builder": "clearskies_doc_builder.builders.Module",
      "parent": "Cursors",
      "classes": ["clearskies.cursors.iam.RdsMysql"]
    },
    {
      "title": "Port Forwarding",
      "source": "clearskies.cursors.port_forwarding.PortForwarder",
      "builder": "clearskies_doc_builder.builders.Module",
      "parent": "Cursors",
      "classes": ["clearskies.cursors.port_forwarding.Ssm"]
    }
  ]
}
```

Note that the "Cursors" entry has no `classes` field - it just creates an index page with the overview from the source class docblock. The child sections ("IAM Cursors" and "Port Forwarding") will appear as sub-navigation items under "Cursors".

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

### Automatic Navigation Ordering

Child entries under a parent are automatically sorted so that submodules appear first (alphabetically), followed by individual classes (alphabetically). The entry type is **automatically inferred** from the builder:

- **`Module` builder** → treated as "submodule" (appears first)
- **`SingleClass` / `SingleClassToSection` builder** → treated as "class" (appears after submodules)
- **Other builders** → appear last

#### Example

```json
{
  "tree": [
    {
      "title": "Cursors",
      "source": "clearskies.cursors.Cursor",
      "builder": "clearskies_doc_builder.builders.Module"
    },
    {
      "title": "Memory Cursor",
      "source": "clearskies.cursors.MemoryCursor",
      "builder": "clearskies_doc_builder.builders.SingleClass",
      "parent": "Cursors"
    },
    {
      "title": "File Cursor",
      "source": "clearskies.cursors.FileCursor",
      "builder": "clearskies_doc_builder.builders.SingleClass",
      "parent": "Cursors"
    },
    {
      "title": "From Environment",
      "source": "clearskies.cursors.from_environment.FromEnvironmentBase",
      "builder": "clearskies_doc_builder.builders.Module",
      "parent": "Cursors",
      "classes": ["clearskies.cursors.from_environment.EnvCursor"]
    },
    {
      "title": "AWS",
      "source": "clearskies.cursors.aws.AWSBase",
      "builder": "clearskies_doc_builder.builders.Module",
      "parent": "Cursors",
      "classes": ["clearskies.cursors.aws.SecretsManager"]
    }
  ]
}
```

This will generate navigation in the following order under "Cursors":
1. **AWS** (Module builder = submodule, alphabetically first)
2. **From Environment** (Module builder = submodule, alphabetically second)
3. **File Cursor** (SingleClass builder = class, alphabetically first)
4. **Memory Cursor** (SingleClass builder = class, alphabetically second)

This ensures a consistent navigation structure where submodules (which typically contain multiple classes) are grouped together at the top, followed by individual class documentation.

#### Manual Override with `entry_type`

If needed, you can explicitly set `entry_type` to override the automatic inference:

```json
{
  "title": "Special Entry",
  "source": "...",
  "builder": "clearskies_doc_builder.builders.SingleClass",
  "parent": "Cursors",
  "entry_type": "submodule"
}
```

Supported values: `"submodule"`, `"class"`, or omit for default behavior.
