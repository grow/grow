"""Base class for the post render hook."""

from grow.extensions.hooks import base_hook


class BasePostRenderHook(base_hook.BaseHook):
    """Base extension for custom extensions."""

    KEY = 'post_render'
    NAME = 'Post Render'

    # pylint: disable=arguments-differ
    def trigger(self, previous_result, doc, raw_content):
        """Trigger the pre render hook."""
        raise NotImplementedError()
