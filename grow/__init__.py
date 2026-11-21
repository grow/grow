import importlib.metadata

try:
    __version__ = importlib.metadata.version('grow')
except importlib.metadata.PackageNotFoundError:
    __version__ = '0.0.0'

# Allow `import grow; grow.Pod`.
from .pods.pods import Pod  # noqa: E402

# Allow `import grow; grow.Preprocessor` for custom preprocessors.
from .preprocessors.base import BasePreprocessor as Preprocessor  # noqa: E402

# Allow `import grow; grow.Translator` for custom translators.
from .translators.base import Translator  # noqa: E402

__all__ = ['Pod', 'Preprocessor', 'Translator', '__version__']
