---
$title: Extensions
$category: Reference
$order: 9
---
# Extensions

[TOC]

Grow has a powerful and simple extension system that enables you to extend the functionality of Grow with plugins.

Extensions are standard Python modules, so your site's `extensions` folder must be set up appropriately, with `__init__.py` files:

[sourcecode:bash]
├──  /extensions*                  # All your extensions
|    ├──  /__init__.py*            # Empty file, required by Python
|    ├──  /triplicate.py           # An example of a Jinja2 extension
|    └──  /preprocessors*          # Subfolder for preprocessor extensions
|         ├──  /__init__.py*       # Empty file, required by Python
|         ├──  /hello.py           # An example of a preprocessor extension
[/sourcecode]


## Jinja2 extensions

Sites can directly extend Grow's Jinja2 rendering environment by including custom Jinja2 extensions. Jinja2 extensions can add site-specific filters, tests, globals, and extend the template parser. [See Jinja2's documentation on extensions](http://jinja.pocoo.org/docs/extensions/).

Specify additional, site-specific Jinja2 extensions in `podspec.yaml`:

[sourcecode:yaml]
# podspec.yaml

extensions:
  jinja2:
  - extensions.triplicate.Triplicate
[/sourcecode]

Define the extension in a corresponding place in the `/extensions/` folder.

[sourcecode:python]
# /extensions/triplicate.py

from jinja2.ext import Extension


def do_triplicate(value):
    return value * 3


class Triplicate(Extension):

    def __init__(self, environment):
        super(Triplicate, self).__init__(environment)
        environment.filters['triplicate'] = do_triplicate
[/sourcecode]

Now you can use your custom `triplicate` filter in your Jinja2 templates.

[sourcecode:yaml]
# /views/base.html

{{10|triplicate}}
[/sourcecode]

## Custom preprocessors

Sites can define custom preprocessors to do pretty much anything at build time and run time. Custom preprocessors can leverage all of the builtin preprocessor controls, such as the `grow preprocess` command, the `--preprocess` flag, and options like `name`, `autorun`, and `tags`.

Specify and use your custom preprocessor in `podspec.yaml`:

[sourcecode:yaml]
# podspec.yaml

extensions:
  preprocessors:
  - extensions.preprocessors.hello.HelloPreprocessor

preprocessors:
- kind: hello
  person: Zoey
[/sourcecode]

Define the preprocessor in a corresponding place in the `/extensions/` folder. Grow preprocessors should subclass `grow.Preprocessor` and use ProtoRPC Messages to define their configuration.

[sourcecode:python]
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
[/sourcecode]

Now, you can use the preprocessor.

[sourcecode:shell]
$ grow preprocess
Hello, Zoey!
[/sourcecode]
