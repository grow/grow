"""Deprecated path for Grow documents."""

# TODO: Remove after deprecation period.

from grow.common import deprecated
from grow.documents import document as new_ref

# Alias constants.
PATH_LOCALE_REGEX = new_ref.PATH_LOCALE_REGEX
BUILT_IN_FIELDS = new_ref.BUILT_IN_FIELDS

# pylint: disable=invalid-name
Error = deprecated.MovedHelper(
    new_ref.Error, 'grow.pods.documents.Error')
DocumentDoesNotExistError = deprecated.MovedHelper(
    new_ref.DocumentDoesNotExistError, 'grow.pods.documents.DocumentDoesNotExistError')
DocumentExistsError = deprecated.MovedHelper(
    new_ref.DocumentExistsError, 'grow.pods.documents.DocumentExistsError')
PathFormatError = deprecated.MovedHelper(
    new_ref.PathFormatError, 'grow.pods.documents.PathFormatError')
Document = deprecated.MovedHelper(
    new_ref.Document, 'grow.pods.documents.Document')
