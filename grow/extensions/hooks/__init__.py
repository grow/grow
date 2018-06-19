"""Extension hooks."""

from . import dev_file_change_hook
from . import dev_handler_hook
from . import post_render_hook
from . import pre_render_hook
from . import preprocess_hook

# pylint: disable=invalid-name
DevFileChangeHook = dev_file_change_hook.DevFileChangeHook
PreprocessHook = preprocess_hook.PreprocessHook

HOOKS = (
    dev_file_change_hook.DevFileChangeHook,
    preprocess_hook.PreprocessHook,
)
