"""Deprecated path for Grow document fields."""

# TODO: Remove after deprecation period.

from grow.common import deprecated
from grow.documents import document_fields as new_ref

# Alias constants.
LOCALIZED_KEY_REGEX = new_ref.LOCALIZED_KEY_REGEX

# pylint: disable=invalid-name
DocumentFields = deprecated.MovedHelper(
    new_ref.DocumentFields, 'grow.pods.document_fields.DocumentFields')
