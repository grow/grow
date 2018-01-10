---
$title: Extensions
$category: Reference
$order: 9
---
[TOC]

Grow has a powerful and simple extension system that enables you to extend the functionality of Grow with plugins.

## Installing extensions

Grow supports an `extensions.txt` file as part of the pod. When the file is present the `grow install` command will handle the installation of the extensions.

```
# extensions.txt
git+git://github.com/grow/grow-ext-contentful
```

The `extensions.txt` follows the same format as a normal pip `requirements.txt` style. This means you can install pip packages or directly from [version control](https://pip.pypa.io/en/stable/reference/pip_install/#vcs-support).

See the documentation for each extension for instructions on how to properly configure the extension and what settings to add to the `podspec.yaml` file.

## Finding extensions

Extensions can be found by either searching pip or [github](https://github.com/search?q=%22grow-ext-%22&type=Repositories&utf8=%E2%9C%93) for `grow-ext-`.

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

### Jinja2 extensions

Sites can directly extend Grow's Jinja2 rendering environment by including custom Jinja2 extensions. Jinja2 extensions can add site-specific filters, tests, globals, and extend the template parser. [See Jinja2's documentation on extensions](http://jinja.pocoo.org/docs/extensions/).

Specify additional, site-specific Jinja2 extensions in `podspec.yaml`:

```yaml
# podspec.yaml
extensions:
  jinja2:
  - extensions.triplicate.triplicate.Triplicate
```

Define the extension in a corresponding place in the `/extensions/` folder.

```python
# /extensions/triplicate/triplicate.py

from jinja2.ext import Extension


def do_triplicate(value):
    return value * 3


class Triplicate(Extension):

    def __init__(self, environment):
        super(Triplicate, self).__init__(environment)
        environment.filters['triplicate'] = do_triplicate
```

Now you can use your custom `triplicate` filter in your Jinja2 templates.

```yaml
# /views/base.html

{{10|triplicate}}
```

### Preprocessors

Sites can define custom preprocessors to do pretty much anything at build time and run time. Custom preprocessors can leverage all of the builtin preprocessor controls, such as the `grow preprocess` command, the `--preprocess` flag, and options like `name`, `autorun`, and `tags`.

Specify and use your custom preprocessor in `podspec.yaml`:

```yaml
# podspec.yaml

extensions:
  preprocessors:
  - extensions.preprocessors.hello.HelloPreprocessor

preprocessors:
- kind: hello
  person: Zoey
```

Define the preprocessor in a corresponding place in the `/extensions/` folder. Grow preprocessors should subclass `grow.Preprocessor` and use ProtoRPC Messages to define their configuration.

```python
# /extensions/preprocessors/hello.py

import grow
from protorpc import messages


class HelloPreprocessor(grow.Preprocessor):
    """Says hello to a person."""

    KIND = 'hello'

    class Config(messages.Message):
        person = messages.StringField(1)

    def run(self, build=True):
        print 'Hello, {}!'.format(self.config.person)
```

Now, you can use the preprocessor.

```bash
$ grow preprocess
Hello, Zoey!
```

### Manual Preprocessors

Some preprocessors should not be run every time the site is built or the development server is started. In these cases a `name` can be added to the config and the `autorun` can be turned off.

```yaml
# podspec.yaml
preprocessors:
- kind: hello
  name: hello
  autorun: false
  person: Zoey
```

To run a specific preprocessor use the `-p` flag:

```bash
$ grow preprocess -p hello
Hello, Zoey!
```
