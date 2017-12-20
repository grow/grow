"""Deprecated path for storage errors."""

# TODO: Remove after deprecation period.

from grow.common import deprecated
from grow.storage import base_storage as new_ref

# pylint: disable=invalid-name
BaseStorage = deprecated.MovedHelper(
    new_ref.BaseStorage, 'grow.pods.storage.base_storage.BaseStorage')
