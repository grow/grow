"""Deprecated path for Grow locales."""

# TODO: Remove after deprecation period.

from grow.common import deprecated
from grow.translations import locales as new_ref

# pylint: disable=invalid-name
Locales = deprecated.MovedHelper(
    new_ref.Locales, 'grow.pods.locales.Locales')
Locale = deprecated.MovedHelper(
    new_ref.Locale, 'grow.pods.locales.Locale')
