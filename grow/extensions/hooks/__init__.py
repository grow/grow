"""Extension hooks."""

from . import dev_file_change_hook
from . import dev_handler_hook
from . import post_render_hook
from . import pre_render_hook
from . import pre_process_hook

# pylint: disable=invalid-name
DevFileChangeHook = dev_file_change_hook.DevFileChangeHook
DevHandlerHook = dev_handler_hook.DevHandlerHook
PostRenderHook = post_render_hook.PostRenderHook
PreRenderHook = pre_render_hook.PreRenderHook
PreProcessHook = pre_process_hook.PreProcessHook

HOOKS = (
    dev_file_change_hook.DevFileChangeHook,
    dev_handler_hook.DevHandlerHook,
    post_render_hook.PostRenderHook,
    pre_render_hook.PreRenderHook,
    pre_process_hook.PreProcessHook,
)
