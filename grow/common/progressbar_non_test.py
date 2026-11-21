"""Tests for grow.common.progressbar_non."""

import io
import unittest

from grow.common import progressbar_non


class ProgressBarTestCase(unittest.TestCase):
    def test_progress_bar_lifecycle(self):
        stream = io.StringIO()
        widgets = [progressbar_non.FormatLabel('Building: %(value)d/3 (in %(elapsed)s)')]
        bar = progressbar_non.ProgressBar(maxval=3, widgets=widgets, stream=stream)
        bar.start()
        bar.update(1)
        bar.update(2)
        bar.finish()
        output = stream.getvalue()
        self.assertIn('Building: 3/3', output)
        self.assertEqual(3, bar.value)
        self.assertEqual(100.0, bar.percentage)
