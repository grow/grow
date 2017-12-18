"""Deprecated path for Grow catalogs."""

from grow.common import deprecated
from grow.translations import catalogs as new_ref

# pylint: disable=invalid-name
Catalog = deprecated.MovedHelper(
    new_ref.Catalog, 'grow.pods.catalogs.Catalog')
