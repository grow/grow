"""Tests for the path filter."""

import unittest
from grow.rendering import render_pipeline
from grow.testing import mocks


class RenderPipelineTestCase(unittest.TestCase):
    """Test the rendering pipline flow."""

    def setUp(self):
        pod = mocks.mock_pod(podspec={
            'root': 'root_path',
        })
        self.pipeline = render_pipeline.RenderPipeline(pod)

    def test_some(self):
        """Default."""
        pass
