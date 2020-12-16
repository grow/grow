"""Deployment core extension."""

from grow import extensions
from grow.extensions import hooks
from grow.deployments.destinations import git_destination
from grow.deployments.destinations import local
from grow.deployments.destinations import webreview_destination


class DeploymentDeploymentRegisterHook(hooks.DeploymentRegisterHook):
    """Handle the deployment registration hook."""

    # pylint: disable=arguments-differ
    def trigger(self, previous_result, deployments, *_args, **_kwargs):
        """Trigger the deployment destination registration hook."""
        deployments.register_destination(
            webreview_destination.WebReviewDestination)
        deployments.register_destination(
            webreview_destination.LegacyJetwayDestination)
        deployments.register_destination(git_destination.GitDestination)
        deployments.register_destination(local.LocalDestination)


# pylint: disable=abstract-method
class DeploymentExtension(extensions.BaseExtension):
    """Extension for handling core deployment functionality."""

    @property
    def available_hooks(self):
        """Returns the available hook classes."""
        return [DeploymentDeploymentRegisterHook]
