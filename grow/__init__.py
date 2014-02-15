import os
import sys
sys.path.extend([os.path.join(os.path.dirname(__file__), '..')])

try:
  from grow import submodules
  submodules.fix_imports()
except ImportError:
  pass
