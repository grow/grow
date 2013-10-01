import os
import sys
sys.path.extend([os.path.join(os.path.dirname(__file__), '..')])
from grow import submodules
submodules.fix_imports()
