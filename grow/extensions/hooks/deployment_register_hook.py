"""Base class for the deployment destination registration hook."""

from grow.extensions.hooks import base_hook


class DeploymentRegisterHook(base_hook.BaseHook):
    """Hook for deployment destination registration."""

    KEY = 'deployment_register'
    NAME = 'Deployment Destination Registration'

    # pylint: disable=arguments-differ,unused-argument
    def trigger(self, previous_result, deployments, *_args, **_kwargs):
        """Trigger the deployment destination registration hook."""
        if previous_result:
            return previous_result
        # Return None if nothing has changed.
        return None
