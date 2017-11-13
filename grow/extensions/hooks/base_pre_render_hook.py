"""Base class for the pre render hook."""

from grow.extensions.hooks import base_hook


class BasePreRenderHook(base_hook.BaseHook):
    """Base extension for custom extensions."""

    KEY = 'pre_render'
    NAME = 'Pre Render'

    # pylint: disable=arguments-differ
    def trigger(self, previous_result, doc, raw_content):
        """Trigger the pre render hook."""
        raise NotImplementedError()
