---
$title: Legacy Extensions
$category: Extensions
$order: 5.1
---
# Legacy Extensions

The following deals with developing legacy Grow extensions. For developing using
the new extension format see the [new extension docs]([url('/content/docs/extensions.md')]).

### Jinja2 extensions

Sites can directly extend Grow's Jinja2 rendering environment by including
custom Jinja2 extensions. Jinja2 extensions can add site-specific filters,
tests, globals, and extend the template parser.

[See Jinja2's documentation on extensions](http://jinja.pocoo.org/docs/extensions/).

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
