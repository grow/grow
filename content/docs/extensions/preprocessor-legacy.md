---
# $title: Legacy Preprocessors
$title: Create Preprocessors
$category: Extensions
$order: 5.3
---
# Legacy Preprocessors

Sites can define custom preprocessors to do pretty much anything at build time
and run time. Custom preprocessors can leverage all of the builtin preprocessor
controls, such as the `grow preprocess` command, the `--preprocess` flag, and
options like `name`, `autorun`, and `tags`.

Specify and use your custom preprocessor in `podspec.yaml`:

```yaml
# podspec.yaml

extensions:
  preprocessors:
  - ext.hello.HelloPreprocessor

preprocessors:
- kind: hello
  person: Zoey
```

Define the preprocessor in the `/ext/` folder.
Grow preprocessors should subclass `grow.Preprocessor` and use ProtoRPC Messages
to define their configuration.

```python
# /ext/hello.py

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

Lastly, in the same `/ext` folder, create an empty file called `__init__.py` to let Grow know that this is a module.

Now, you can use the preprocessor.

```bash
$ grow preprocess
Hello, Zoey!
```
