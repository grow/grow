"""Deprecated path for Grow document front matter."""

from grow.common import deprecated
from grow.documents import document_front_matter as new_ref

# pylint: disable=invalid-name
Error = deprecated.MovedHelper(
    new_ref.Error, 'grow.pods.documents.Error')
BadFormatError = deprecated.MovedHelper(
    new_ref.BadFormatError, 'grow.pods.documents.BadFormatError')
DocumentFrontMatter = deprecated.MovedHelper(
    new_ref.DocumentFrontMatter, 'grow.pods.documents.DocumentFrontMatter')
