"""Extension hooks."""

from . import base_pre_render_hook
from . import base_post_render_hook

# pylint: disable=invalid-name
BasePostRenderHook = base_post_render_hook.BasePostRenderHook
BasePreRenderHook = base_pre_render_hook.BasePreRenderHook

HOOKS = (
    base_post_render_hook.BasePostRenderHook,
    base_pre_render_hook.BasePreRenderHook,
)
