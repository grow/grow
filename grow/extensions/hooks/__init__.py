"""Extension hooks."""

from . import base_dev_file_change_hook
from . import base_dev_handler_hook
from . import base_post_render_hook

# pylint: disable=invalid-name
BaseDevFileChangeHook = base_dev_file_change_hook.BaseDevFileChangeHook
BaseDevHandlerHook = base_dev_handler_hook.BaseDevHandlerHook
BasePostRenderHook = base_post_render_hook.BasePostRenderHook

HOOKS = (
    base_dev_file_change_hook.BaseDevFileChangeHook,
    base_dev_handler_hook.BaseDevHandlerHook,
    base_post_render_hook.BasePostRenderHook,
)
