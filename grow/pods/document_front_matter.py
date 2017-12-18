"""Deprecated path for Grow document front matter."""

# TODO: Remove after deprecation period.

from grow.common import deprecated
from grow.documents import document_front_matter as new_ref

# Alias constants.
BOUNDARY_REGEX = new_ref.BOUNDARY_REGEX
CONVERT_MESSAGE = new_ref.CONVERT_MESSAGE

# pylint: disable=invalid-name
Error = deprecated.MovedHelper(
    new_ref.Error, 'grow.pods.document_front_matter.Error')
BadFormatError = deprecated.MovedHelper(
    new_ref.BadFormatError, 'grow.pods.document_front_matter.BadFormatError')
DocumentFrontMatter = deprecated.MovedHelper(
    new_ref.DocumentFrontMatter, 'grow.pods.document_front_matter.DocumentFrontMatter')
