"""Extension hooks."""

from . import dev_file_change_hook
from . import dev_handler_hook
from . import post_render_hook
from . import pre_deploy_hook
from . import pre_render_hook
from . import pre_process_hook

# pylint: disable=invalid-name
DevFileChangeHook = dev_file_change_hook.DevFileChangeHook
DevHandlerHook = dev_handler_hook.DevHandlerHook
PostRenderHook = post_render_hook.PostRenderHook
PreDeployHook = pre_deploy_hook.PreDeployHook
PreRenderHook = pre_render_hook.PreRenderHook
PreProcessHook = pre_process_hook.PreProcessHook
PreprocessHook = pre_process_hook.PreProcessHook  # Legacy support.

HOOKS = (
    dev_file_change_hook.DevFileChangeHook,
    dev_handler_hook.DevHandlerHook,
    post_render_hook.PostRenderHook,
    pre_deploy_hook.PreDeployHook,
    pre_render_hook.PreRenderHook,
    pre_process_hook.PreProcessHook,
)


def generator_wrapper(pod, hook_name, generator, *args, **kwargs):
    """Wrap the output from a generator to do a simple trigger an extension hook."""
    # Make any changes necessary before deploying.
    for item in generator:
        pod.extensions_controller.trigger(hook_name, item, *args, **kwargs)
        yield item
