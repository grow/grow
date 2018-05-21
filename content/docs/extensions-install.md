---
$title: Installing Extensions
$category: Extensions
$order: 5.0
---
[TOC]

Grow has a powerful and simple extension system that enables you to extend the
functionality of Grow with extensions.

## Installing extensions

Grow supports an `extensions.txt` file as part of the pod. When the file is
present the `grow install` command will handle the installation of the
extensions.

```txt
# extensions.txt
git+git://github.com/grow/grow-ext-contentful
```

The `extensions.txt` follows the same format as a normal pip `requirements.txt`
style. This means you can install pip packages or directly from
[version control][vcs].

See the documentation for each extension for instructions on how to properly
configure the extension and what settings to add to the `podspec.yaml` file.

## Finding extensions

Extensions can be found by searching for `grow-ext-` in [pypi][pypi] or
[github][github].

## Custom Extensions

When possible, extensions should be created as separate repositories and use the `extensions.txt` file to reference the extension. This helps the extensions be reusable across projects.

Repositories for grow extensions should be named using the `grow-ext-<extension name>` format. For example: [grow-ext-budou](https://github.com/grow/grow-ext-budou), [grow-ext-google-forms](https://github.com/grow/grow-ext-google-forms), [grow-ext-contentful](https://github.com/grow/grow-ext-contentful).

In some cases it makes more sense to write the extension inside the same repository as it is very specific to the site. The same principles apply just put the extension files into a subdirectory inside the `extensions/` directory.

Extensions are standard Python modules, so your site's `extensions` folder must be set up appropriately, with `__init__.py` files:

```bash
├──  /extensions                   # All your extensions
|    ├──  /__init__.py             # Empty file, required by Python
|    └──  /extension_name          # Subfolder for custom extension
|         ├──  /__init__.py        # Empty file, required by Python
|         ├──  /extension_name.py  # Extension code
```

[vcs]: https://pip.pypa.io/en/stable/reference/pip_install/#vcs-support
[pypi]: https://pypi.org/search/?q=grow-ext-
[github]: https://github.com/search?q=%22grow-ext-%22&type=Repositories&utf8=%E2%9C%93
