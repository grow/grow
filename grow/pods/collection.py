"""Deprecated path for Grow collection."""

# TODO: Remove after deprecation period.

from grow.common import deprecated
from grow.collections import collection as new_ref

# pylint: disable=invalid-name
Error = deprecated.MovedHelper(
    new_ref.Error, 'grow.pods.collections.Error')
BadCollectionNameError = deprecated.MovedHelper(
    new_ref.BadCollectionNameError, 'grow.pods.collections.BadCollectionNameError')
BadFieldsError = deprecated.MovedHelper(
    new_ref.BadFieldsError, 'grow.pods.collections.BadFieldsError')
CollectionDoesNotExistError = deprecated.MovedHelper(
    new_ref.CollectionDoesNotExistError, 'grow.pods.collections.CollectionDoesNotExistError')
CollectionExistsError = deprecated.MovedHelper(
    new_ref.CollectionExistsError, 'grow.pods.collections.CollectionExistsError')
CollectionNotEmptyError = deprecated.MovedHelper(
    new_ref.CollectionNotEmptyError, 'grow.pods.collections.CollectionNotEmptyError')
NoLocalesError = deprecated.MovedHelper(
    new_ref.NoLocalesError, 'grow.pods.collections.NoLocalesError')
Collection = deprecated.MovedHelper(
    new_ref.Collection, 'grow.pods.collections.Collection')
