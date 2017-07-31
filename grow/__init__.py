import os
import sys

# Allows "import grow" and "from grow import <name>".
sys.path.extend([os.path.join(os.path.dirname(__file__), '..')])

# Set up path for make test-gae.
if 'NOSEGAE' in os.environ:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib')))

# Allow `import grow; grow.Pod`.
from .pods.pods import Pod

# Allow `import grow; grow.Preprocessor` for custom preprocessors.
from .preprocessors.base import BasePreprocessor as Preprocessor

# Allow `import grow; grow.Translator` for custom translators.
from .translators.base import Translator

# Allow `import grow; grow.FrozenImportFixer`.
from .common.extensions import FrozenImportFixer
