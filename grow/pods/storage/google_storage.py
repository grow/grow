"""Deprecated path for GCS storage."""

# TODO: Remove after deprecation period.

from grow.common import deprecated
from grow.storage import google_storage as new_ref

# pylint: disable=invalid-name
CloudStorage = deprecated.MovedHelper(
    new_ref.CloudStorage, 'grow.pods.storage.google_storage.CloudStorage')
CloudStorageLoader = deprecated.MovedHelper(
    new_ref.CloudStorageLoader, 'grow.pods.storage.google_storage.CloudStorageLoader')
