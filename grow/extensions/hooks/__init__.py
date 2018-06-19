"""Extension hooks."""

from . import dev_file_change_hook
from . import dev_handler_hook
from . import preprocess_hook

# pylint: disable=invalid-name
DevFileChangeHook = dev_file_change_hook.DevFileChangeHook
DevHandlerHook = dev_handler_hook.DevHandlerHook
PreprocessHook = preprocess_hook.PreprocessHook

HOOKS = (
    dev_file_change_hook.DevFileChangeHook,
    dev_handler_hook.DevHandlerHook,
    preprocess_hook.PreprocessHook,
)
