"""Deprecated path for Grow document format."""

# TODO: Remove after deprecation period.

from grow.common import deprecated
from grow.documents import document_format as new_ref

# Alias constants.
BOUNDARY_SEPARATOR = new_ref.BOUNDARY_SEPARATOR

# pylint: disable=invalid-name
Error = deprecated.MovedHelper(
    new_ref.Error, 'grow.pods.document_format.Error')
BadFormatError = deprecated.MovedHelper(
    new_ref.BadFormatError, 'grow.pods.document_format.BadFormatError')
BadLocalesError = deprecated.MovedHelper(
    new_ref.BadLocalesError, 'grow.pods.document_format.BadLocalesError')
DocumentFormat = deprecated.MovedHelper(
    new_ref.DocumentFormat, 'grow.pods.document_format.DocumentFormat')
HtmlDocumentFormat = deprecated.MovedHelper(
    new_ref.HtmlDocumentFormat, 'grow.pods.document_format.HtmlDocumentFormat')
MarkdownDocumentFormat = deprecated.MovedHelper(
    new_ref.MarkdownDocumentFormat, 'grow.pods.document_format.MarkdownDocumentFormat')
TextDocumentFormat = deprecated.MovedHelper(
    new_ref.TextDocumentFormat, 'grow.pods.document_format.TextDocumentFormat')
YamlDocumentFormat = deprecated.MovedHelper(
    new_ref.YamlDocumentFormat, 'grow.pods.document_format.YamlDocumentFormat')
