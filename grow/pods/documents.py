"""Deprecated path for Grow documents."""

from grow.common import deprecated
from grow.documents import documents as new_ref

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
