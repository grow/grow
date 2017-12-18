"""Deprecated path for Grow document fields."""

from grow.common import deprecated
from grow.documents import document_fields as new_ref

# pylint: disable=invalid-name
DocumentFields = deprecated.MovedHelper(
    new_ref.DocumentFields, 'grow.pods.document_fields.DocumentFields')
