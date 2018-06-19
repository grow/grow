"""Base class for the post render hook."""

from grow.extensions.hooks import base_hook


class PostRenderHook(base_hook.BaseHook):
    """Hook for post render."""

    KEY = 'post_render'
    NAME = 'Post Render'

    # pylint: disable=arguments-differ,unused-argument
    def trigger(self, previous_result, doc, raw_content, *_args, **_kwargs):
        """Trigger the post render hook."""
        return previous_result
