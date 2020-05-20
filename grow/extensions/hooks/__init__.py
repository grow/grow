"""Extension hooks."""

from . import deployment_register_hook
from . import dev_file_change_hook
from . import dev_handler_hook
from . import dev_manager_message_hook
from . import jinja_env_init_hook
from . import jinja_extension_hook
from . import post_render_hook
from . import pre_deploy_hook
from . import pre_render_hook
from . import pre_process_hook
from . import podspec_static_dir_hook
from . import router_add_hook
from . import stub_hook

# pylint: disable=invalid-name
DeploymentRegisterHook = deployment_register_hook.DeploymentRegisterHook
DevFileChangeHook = dev_file_change_hook.DevFileChangeHook
DevHandlerHook = dev_handler_hook.DevHandlerHook
DevManagerMessageHook = dev_manager_message_hook.DevManagerMessageHook
JinjaEnvInitHook = jinja_env_init_hook.JinjaEnvInitHook
JinjaExtensionHook = jinja_extension_hook.JinjaExtensionHook
PodspecStaticDirHook = podspec_static_dir_hook.PodspecStaticDirHook
PostRenderHook = post_render_hook.PostRenderHook
PreDeployHook = pre_deploy_hook.PreDeployHook
PreRenderHook = pre_render_hook.PreRenderHook
PreProcessHook = pre_process_hook.PreProcessHook
PreprocessHook = pre_process_hook.PreProcessHook  # Legacy support.
RouterAddHook = router_add_hook.RouterAddHook
StubHook = stub_hook.StubHook

HOOKS = (
    DeploymentRegisterHook,
    DevFileChangeHook,
    DevHandlerHook,
    DevManagerMessageHook,
    JinjaEnvInitHook,
    JinjaExtensionHook,
    PodspecStaticDirHook,
    PostRenderHook,
    PreDeployHook,
    PreRenderHook,
    PreProcessHook,
    RouterAddHook,
)


def generator_wrapper(pod, hook_name, generator, *args, **kwargs):
    """Wrap the output from a generator to do a simple trigger an extension hook."""
    # Make any changes necessary before deploying.
    for item in generator:
        pod.extensions_controller.trigger(hook_name, item, *args, **kwargs)
        yield item
