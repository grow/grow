"""Deprecated path for storage errors."""

# TODO: Remove after deprecation period.

from grow.common import deprecated
from grow.storage import errors as new_ref

# pylint: disable=invalid-name
Error = deprecated.MovedHelper(
    new_ref.Error, 'grow.pods.storage.errors.Error')
PathError = deprecated.MovedHelper(
    new_ref.PathError, 'grow.pods.storage.errors.PathError')
NotFoundError = deprecated.MovedHelper(
    new_ref.NotFoundError, 'grow.pods.storage.errors.NotFoundError')
