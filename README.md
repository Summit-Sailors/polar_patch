# Polar Patch

This package provides type hinting and IDE support for plugins to the Polars package, enhancing the development experience.

## Problem It Solves

Polars is a fast DataFrame library for Python, but it lacks a way to provide type hints with type checker and IDE support for custom plugins. The polars maintainers have no plans to fill this gap from within polars itself. So Summit Sailors is stepping in to help.

## Motivation

With this package, developers can:

- Write more robust and maintainable polars plugins.
- Utilize IDE Type Checker features such as autocompletion and inline documentation.
- Extend the polars ecosystem with more incentive to create new plugins

## How does it work?

Polar Patch uses libCST to extract info about your plugin. It then adds the appropriate attribute with type hint onto the correcsponding polars class in the site-packages of the interpreter running the command. The correspondingimport is inserted into a type checking block to avoid circular dep issues. It is important to note that while this is minimally invasive, it is monkey patching your interpreters polars package.

![Added Attribute](images/attr_type_hint_added.png)

![Added Import](images/attr_type_hint_import.png)

## Status

This package is currently in alpha and PRs are welcome. Only classes registered with the `@pl.api` decorator are currently supported. Lack of support for the callable form of `pl.api` is seen as a blocker for a beta release. Also, many edge cases have not been addressed such as removing redundancy, ie if u run it twice the attr will be added twice. This is another blocker for a beta release. There is bare minimum direct testing. Thorough testing is a blocker for a stable release.

## Installation

```bash
pip install polar-patch
```

## Configuration

To specify paths to be scanned for plugins, create a polar_patch.toml file in your project root.
(VSC IDE Support in Development)

```toml
[polar_patch]
scan_paths = ["path/to/your/plugin1.py", "path/to/your/polars/plugin/folder"]
```

## Usage

To use the CLI tool provided by this package, run the following command:

```bash
pp mount
```

## Undoing Changes

If you need to undo the changes made by this package, simply reinstall the Polars package in your interpreter:

```bash
pip uninstall polars
pip install polars
```
