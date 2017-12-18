"""Deprecated path for Grow document format."""

from grow.common import deprecated
from grow.documents import document_format as new_ref

# pylint: disable=invalid-name
Error = deprecated.MovedHelper(
    new_ref.Error, 'grow.pods.documents.Error')
BadFormatError = deprecated.MovedHelper(
    new_ref.BadFormatError, 'grow.pods.documents.BadFormatError')
BadLocalesError = deprecated.MovedHelper(
    new_ref.BadLocalesError, 'grow.pods.documents.BadLocalesError')
DocumentFormat = deprecated.MovedHelper(
    new_ref.DocumentFormat, 'grow.pods.documents.DocumentFormat')
HtmlDocumentFormat = deprecated.MovedHelper(
    new_ref.HtmlDocumentFormat, 'grow.pods.documents.HtmlDocumentFormat')
MarkdownDocumentFormat = deprecated.MovedHelper(
    new_ref.MarkdownDocumentFormat, 'grow.pods.documents.MarkdownDocumentFormat')
TextDocumentFormat = deprecated.MovedHelper(
    new_ref.TextDocumentFormat, 'grow.pods.documents.TextDocumentFormat')
YamlDocumentFormat = deprecated.MovedHelper(
    new_ref.YamlDocumentFormat, 'grow.pods.documents.YamlDocumentFormat')
