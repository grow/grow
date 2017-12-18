"""Deprecated path for Grow catalog holder."""

# TODO: Remove after deprecation period.

from grow.common import deprecated
from grow.translations import catalog_holder as new_ref

# pylint: disable=invalid-name
Error = deprecated.MovedHelper(
    new_ref.Error, 'grow.pods.catalog_holder.Error')
UsageError = deprecated.MovedHelper(
    new_ref.UsageError, 'grow.pods.catalog_holder.UsageError')
Catalogs = deprecated.MovedHelper(
    new_ref.Catalogs, 'grow.pods.catalog_holder.Catalogs')
