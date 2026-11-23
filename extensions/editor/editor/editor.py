"""Editor extension for editing content in Grow."""

from grow import extensions
from grow.common import colors
from grow.extensions import hooks
from grow.routing import router as grow_router

from . import editor_api, handlers

try:
    DevManagerMessageHook = hooks.DevManagerMessageHook
except AttributeError:
    try:
        DevManagerMessageHook = hooks.StubHook
    except AttributeError:
        from grow.extensions.hooks import base_hook

        DevManagerMessageHook = base_hook.BaseHook


class EditorDevHandlerHook(hooks.DevHandlerHook):
    """Handle the dev handler hook."""

    def trigger(self, previous_result, routes, host='localhost', port=8080, *_args, **_kwargs):
        """Execute dev handler modification."""
        routes.add(
            '/_grow/api/editor/*path',
            grow_router.RouteInfo(
                'console',
                meta={
                    'handler': editor_api.serve_api,
                },
            ),
        )

        editor_meta = {
            'handler': handlers.serve_editor,
            'meta': {
                'app': {
                    'host': host,
                    'port': port,
                },
            },
        }
        routes.add('/_grow/editor/*path', grow_router.RouteInfo('console', meta=editor_meta))
        routes.add('/_grow/editor', grow_router.RouteInfo('console', meta=editor_meta))

        preview_meta = {
            'handler': handlers.serve_preview_server,
            'meta': {
                'app': {
                    'host': host,
                    'port': port,
                },
            },
        }
        routes.add('/preview.json', grow_router.RouteInfo('console', meta=preview_meta))


class EditorDevManagerMessageHook(DevManagerMessageHook):
    """Handle the dev manager message hook."""

    def trigger(self, previous_result, display_func, url_base, url_root, *_args, **_kwargs):
        url_editor = f'{url_base}_grow/editor'
        display_func('Editor:', url_editor, colors.HIGHLIGHT)
        previous_result = previous_result or []
        previous_result.append(url_editor)
        return previous_result


class EditorPodspecStaticDirHook(hooks.PodspecStaticDirHook):
    """Handle the static dir hook."""

    def trigger(self, previous_result, *_args, **_kwargs):
        previous_result = previous_result or []
        if not self.extension.config.get('enabled', True):
            return previous_result

        previous_result.append(
            {
                'static_dir': '/extensions/editor/dist/',
                'serve_at': '/_grow/ext/editor/',
                'fingerprinted': True,
            }
        )
        return previous_result


class EditorExtension(extensions.BaseExtension):
    """Editor extension."""

    @property
    def available_hooks(self):
        return [
            EditorDevHandlerHook,
            EditorPodspecStaticDirHook,
            EditorDevManagerMessageHook,
        ]
