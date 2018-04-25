"""Routes core extension."""

from grow import extensions
from grow.extensions import hooks
from grow.pods import ui
from grow.routing import router as grow_router
from werkzeug import wrappers


class RoutesDevHandlerHook(hooks.BaseDevHandlerHook):
    """Handle the dev handler hook."""

    @staticmethod
    def serve_routes(pod, _request, _matched, **_kwargs):
        """Handle the request for routes."""
        env = ui.create_jinja_env()
        template = env.get_template('views/base-reroute.html')
        router = grow_router.Router(pod)
        router.use_simple()
        router.add_all()
        kwargs = {
            'pod': pod,
            'partials': [{
                'partial': 'routes',
                'routes': router.routes,
            }],
            'title': 'Pod Routes',
        }
        content = template.render(kwargs)
        response = wrappers.Response(content)
        response.headers['Content-Type'] = 'text/html'
        return response

    # pylint: disable=arguments-differ
    def trigger(self, _result, _pod, routes, *_args, **_kwargs):
        """Execute dev handler modification."""
        routes.add('/_grow/routes', grow_router.RouteInfo('console', {
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
