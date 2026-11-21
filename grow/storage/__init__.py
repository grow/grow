"""References for all pod storage."""

from grow.storage.errors import Error, NotFoundError, PathError
from grow.storage.file_storage import FileStorage

AUTO = FileStorage

__all__ = ['AUTO', 'Error', 'FileStorage', 'NotFoundError', 'PathError']
