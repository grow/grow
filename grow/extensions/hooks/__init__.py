"""Extension hooks."""

from . import base_dev_handler_hook
from . import base_pre_render_hook
from . import base_post_render_hook

# pylint: disable=invalid-name
BaseDevHandlerHook = base_dev_handler_hook.BaseDevHandlerHook
BasePostRenderHook = base_post_render_hook.BasePostRenderHook
BasePreRenderHook = base_pre_render_hook.BasePreRenderHook

HOOKS = (
    base_dev_handler_hook.BaseDevHandlerHook,
    base_post_render_hook.BasePostRenderHook,
    base_pre_render_hook.BasePreRenderHook,
)
