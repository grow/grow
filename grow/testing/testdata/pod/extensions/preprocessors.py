import grow
from protorpc import messages

# NOTE: This is an unused import, specifically added to verify the ability to
# load extensions that depend on modules in Python's standard library, which
# Grow itself may not depend on.
from . import dependency
import importlib


# Add extra verification for the FrozenImportFixer.
with grow.common.extensions.FrozenImportFixer():
    from . import dependency
    importlib.reload(dependency)


class CustomPreprocessor(grow.Preprocessor):
    KIND = 'custom_preprocessor'

    class Config(messages.Message):
        value = messages.StringField(1)

    def run(self, **kwargs):
        # To allow the test to check the result
        self.pod._custom_preprocessor_value = self.config.value
