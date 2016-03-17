---
$title: Extensions
$category: Reference
$order: 100
---
# Extensions

[TOC]

Grow has a powerful and simple extension system that enables you to extend the functionality of Grow with plugins.

## Jinja2 extensions

Sites can directly extend Grow's Jinja2 rendering environment by including custom Jinja2 extensions. Jinja2 extensions can add site-specific filters, tests, globals, and extend the template parser. [See Jinja2's documentation on extensions](http://jinja.pocoo.org/docs/extensions/).

Specify additional, site-specific Jinja2 extensions in `podspec.yaml`:

[sourcecode:yaml]
# podspec.yaml

extensions:
  jinja2:
  - extensions.triplicate.Triplicate
[/sourcecode]

Define the extension in a corresponding `/extensions/` folder.

[sourcecode:python]
# /extensions/triplicate.py

import jinja2


def do_triplicate(value):
    return value * 3


class Triplicate(jinja2.Extension):

    def __init__(self, environment):
        super(ClassName, self).__init__(environment)
        environment.filters['triplicate'] = do_triplicate
[/sourcecode]

Now you can use your custom `triplicate` filter in your Jinja2 templates.

[sourcecode:yaml]
# /views/base.html

{{10|triplicate}}
[/sourcecode]

## Custom preprocessors

Sites can define custom preprocessors to do pretty much anything at build time and run time. Custom preprocessors can leverage all of the builtin preprocessor controls, such as the `grow preprocess` command, the `--preprocess` flag, and options like `name`, `autorun`, and `tags`.

Specify and use your site-specific preprocessor in `podspec.yaml`:

[sourcecode:yaml]
# podspec.yaml

extensions:
  preprocessors:
  - extensions.preprocessors.print_color.PrintColorPreprocessor

preprocessors:
- kind: print_color
  color: red
[/sourcecode]

Define the preprocessor in a corresponding place in the `/extensions/` folder. Grow preprocessors should subclass the `grow.Preprocessor` class and use ProtoRPC Messages to define their configuration.

[sourcecode:python]
# /extensions/preprocessors/print_color.py

import grow
from protorpc import messages


class PrintColorPreprocessor(grow.Preprocessor):
    """Prints a color defined by the user."""

    KIND = 'print_color'

    class Config(messages.Message):
        color = messages.StringField(1)

    def run(self, build=True):
        print self.config.color
[/sourcecode]
