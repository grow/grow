"""Tests for deprecation helpers."""

import unittest
import mock
from grow.common import deprecated
from grow.common import urls


class MovedHelperTestCase(unittest.TestCase):
    """Test the terminal colors."""

    # pylint: disable=no-self-use
    def test_moved(self):
        """Warning message when the class has moved."""
        mock_warn = mock.Mock()
        test_class = deprecated.MovedHelper(urls.Url, 'grow.common.urls.Url', warn=mock_warn)
        _ = test_class('/')
        mock_warn.assert_called_with(
            'The grow.common.urls.Url class has moved to grow.common.urls.Url and '
            'will be removed in a future version.')

    # pylint: disable=no-self-use
    def test_static_method(self):
        """Moved warning also works with static methods."""
        mock_warn = mock.Mock()
        test_class = deprecated.MovedHelper(urls.Url, 'grow.common.urls.Url', warn=mock_warn)
        _ = test_class.create_relative_path('/foo/bar/baz/', relative_to='/test/dir/')
        mock_warn.assert_called_with(
            'The grow.common.urls.Url class has moved to grow.common.urls.Url and '
            'will be removed in a future version.')
