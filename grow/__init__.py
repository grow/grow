import os
import sys

# Allow easy import for custom preprocessors: `from grow import Preprocessor`
from grow.pods.preprocessors.base import BasePreprocessor as Preprocessor

# Allows "import grow" and "from grow import <name>".
sys.path.extend([os.path.join(os.path.dirname(__file__), '..')])
