"""Extension hooks."""

from . import dev_file_change_hook
from . import dev_handler_hook
from . import post_render_hook
from . import pre_deploy_hook
from . import pre_render_hook
from . import pre_process_hook
from . import podspec_static_dir_hook
from . import router_add_hook

# pylint: disable=invalid-name
DevFileChangeHook = dev_file_change_hook.DevFileChangeHook
DevHandlerHook = dev_handler_hook.DevHandlerHook
PodspecStaticDirHook = podspec_static_dir_hook.PodspecStaticDirHook
PostRenderHook = post_render_hook.PostRenderHook
PreDeployHook = pre_deploy_hook.PreDeployHook
PreRenderHook = pre_render_hook.PreRenderHook
PreProcessHook = pre_process_hook.PreProcessHook
PreprocessHook = pre_process_hook.PreProcessHook  # Legacy support.
RouterAddHook = router_add_hook.RouterAddHook

HOOKS = (
    dev_file_change_hook.DevFileChangeHook,
    dev_handler_hook.DevHandlerHook,
    podspec_static_dir_hook.PodspecStaticDirHook,
    post_render_hook.PostRenderHook,
    pre_deploy_hook.PreDeployHook,
    pre_render_hook.PreRenderHook,
    pre_process_hook.PreProcessHook,
    router_add_hook.RouterAddHook,
)


def generator_wrapper(pod, hook_name, generator, *args, **kwargs):
    """Wrap the output from a generator to do a simple trigger an extension hook."""
    # Make any changes necessary before deploying.
    for item in generator:
        pod.extensions_controller.trigger(hook_name, item, *args, **kwargs)
        yield item
