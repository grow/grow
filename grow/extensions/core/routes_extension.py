"""Routes core extension."""

from grow import extensions
from grow.extensions import hooks
from grow.pods import ui
from grow.routing import router
from werkzeug import wrappers


class RoutesDevHandlerHook(hooks.BaseDevHandlerHook):
    """Handle the dev handler hook."""

    @staticmethod
    def serve_routes(pod, _request, _matched):
        """Handle the request for routes."""
        env = ui.create_jinja_env()
        template = env.get_template('views/base-reroute.html')
        kwargs = {
            'pod': pod,
            'partials': [{
                'partial': 'routes',
                'routes': pod.router.routes,
            }],
            'title': 'Pod Routes',
        }
        content = template.render(kwargs)
        response = wrappers.Response(content)
        response.headers['Content-Type'] = 'text/html'
        return response

    # pylint: disable=arguments-differ
    def trigger(self, _result, pod, routes, *_args, **_kwargs):
        """Execute dev handler modification."""
        routes.add('/_grow/routes', router.RouteInfo('console', {
            'handler': RoutesDevHandlerHook.serve_routes,
        }))


# pylint: disable=abstract-method
class RoutesExtension(extensions.BaseExtension):
    """Extension for handling core routes functionality."""

    @property
    def available_hooks(self):
        """Returns the available hook classes."""
        return [RoutesDevHandlerHook]

    def dev_handler_hook(self):
        """Hook handler for dev handler."""
        return RoutesDevHandlerHook(self)
