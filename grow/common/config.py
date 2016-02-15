import os
import sys

try:
    VERSION = open(os.path.join(sys._MEIPASS, 'VERSION')).read().strip()
except AttributeError:
    VERSION = open(os.path.join(os.path.dirname(__file__), '..', 'VERSION')).read().strip()
