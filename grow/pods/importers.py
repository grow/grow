"""Deprecated path for Grow importers."""

# TODO: Remove after deprecation period.

from grow.common import deprecated
from grow.translations import importers as new_ref

# pylint: disable=invalid-name
Error = deprecated.MovedHelper(
    new_ref.Error, 'grow.pods.importers.Error')
Importer = deprecated.MovedHelper(
    new_ref.Importer, 'grow.pods.importers.Importer')
