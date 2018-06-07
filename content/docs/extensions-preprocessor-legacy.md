---
# $title: Legacy Preprocessors
$title: Create Preprocessors
$category: Extensions
$order: 5.3
---
[TOC]

Sites can define custom preprocessors to do pretty much anything at build time
and run time. Custom preprocessors can leverage all of the builtin preprocessor
controls, such as the `grow preprocess` command, the `--preprocess` flag, and
options like `name`, `autorun`, and `tags`.

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

Define the preprocessor in a corresponding place in the `/extensions/` folder.
Grow preprocessors should subclass `grow.Preprocessor` and use ProtoRPC Messages
to define their configuration.

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
