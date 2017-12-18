"""Deprecated path for file storage."""

# TODO: Remove after deprecation period.

from grow.common import deprecated
from grow.storage import file_storage as new_ref

# pylint: disable=invalid-name
FileStorage = deprecated.MovedHelper(
    new_ref.FileStorage, 'grow.pods.storage.file_storage.FileStorage')
