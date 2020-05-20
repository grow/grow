"""Base class for the jinja environment init hook."""

from grow.extensions.hooks import base_hook


class JinjaEnvInitHook(base_hook.BaseHook):
    """Hook for jinja extension."""

    KEY = 'jinja_env_init'
    NAME = 'Jinja Environment Init'

    # pylint: disable=arguments-differ,unused-argument
    def trigger(self, previous_result, env, *_args, **_kwargs):
        """Trigger the hook."""
        if previous_result:
            return previous_result
        return None
