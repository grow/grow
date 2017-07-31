# Verify ability to include dependencies with extensions. The following import
# examples were known to cause issues with the PyInstaller distribution.
from exceptions import ReferenceError
import copy
import shelve
