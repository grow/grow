"""Routes core extension."""

import os
from werkzeug import wrappers
from grow import extensions
from grow.collections import collection
from grow.common import timer
from grow.extensions import hooks
from grow.performance import docs_loader
from grow.pods import ui
from grow.routing import router as grow_router
from grow.server import handlers


class RoutesDevHandlerHook(hooks.DevHandlerHook):
    """Handle the dev handler hook."""

    @staticmethod
    def _create_response(pod, routes, title, concrete=True):
        env = ui.create_jinja_env()
        template = env.get_template('views/base.html')
        kwargs = {
            'pod': pod,
            'partials': [{
                'partial': 'routes',
                'concrete': concrete,
                'routes': routes,
            }],
            'title': title,
        }
        content = template.render(kwargs)
        response = wrappers.Response(content)
        response.headers['Content-Type'] = 'text/html'
        return response

    @staticmethod
    def serve_routes_abstract(pod, _request, _matched, **_kwargs):
        """Handle the request for abstract routes."""
        routes = pod.router.routes
        return RoutesDevHandlerHook._create_response(
            pod, routes, 'Pod Abstract Routes')

    @staticmethod
    def serve_routes_concrete(pod, _request, _matched, **_kwargs):
        """Handle the request for routes."""
        router = grow_router.Router(pod)
        router.use_simple()
        router.add_all(concrete=True, use_cache=False)
        routes = router.routes
        return RoutesDevHandlerHook._create_response(
            pod, routes, 'Pod Routes')

    # pylint: disable=arguments-differ
    def trigger(self, previous_result, routes, *_args, **_kwargs):
        """Execute dev handler modification."""
        routes.add('/_grow/ui/tools/:tool', grow_router.RouteInfo(
            'console', meta={
                'handler': handlers.serve_ui_tool,
            }))
        routes.add('/_grow', grow_router.RouteInfo('console', meta={
            'handler': handlers.serve_console,
        }))

        routes.add('/_grow/routes', grow_router.RouteInfo(
            'console', meta={
                'handler': RoutesDevHandlerHook.serve_routes_concrete,
            }))
        routes.add('/_grow/routes/concrete', grow_router.RouteInfo(
            'console', meta={
                'handler': RoutesDevHandlerHook.serve_routes_concrete,
            }))
        routes.add('/_grow/routes/abstract', grow_router.RouteInfo(
            'console', meta={
                'handler': RoutesDevHandlerHook.serve_routes_abstract,
            }))


class RoutesDevFileChangeHook(hooks.DevFileChangeHook):
    """Handle the dev file change hook."""

    @staticmethod
    def _reset_routes(pod):
        with timer.Timer() as router_time:
            pod.router.routes.reset()
            pod.router.add_all(concrete=False, use_cache=False)
            # Trigger the dev handler hook.
            pod.extensions_controller.trigger(
                'dev_handler', pod.router.routes)
        pod.logger.info('{} routes rebuilt in {:.3f} s'.format(
            len(pod.router.routes), router_time.secs))

    def trigger(self, previous_result, pod_path, *_args, **_kwargs):
        """Trigger the file change hook."""
        pod = self.pod
        basename = os.path.basename(pod_path)
        ignore_doc = basename.startswith(collection.Collection.IGNORE_INITIAL)

        if pod_path == '/{}'.format(pod.FILE_PODSPEC):
            self._reset_routes(pod)
        elif (pod_path.endswith(collection.Collection.BLUEPRINT_PATH)
              and pod_path.startswith(collection.Collection.CONTENT_PATH)):
            self._reset_routes(pod)
        elif pod_path.startswith(collection.Collection.CONTENT_PATH) and not ignore_doc:
            trigger_doc = pod.get_doc(pod_path)
            col = trigger_doc.collection
            base_docs = []
            original_docs = []
            trigger_docs = col.list_servable_document_locales(pod_path)

            for dep_path in pod.podcache.dependency_graph.get_dependents(pod_path):
                base_docs.append(pod.get_doc(dep_path))
                original_docs += col.list_servable_document_locales(dep_path)

            # Normally this would be part of the podcache extension.
            # Needs to be between retrieving the original docs and flushing
            # the cache to be able to compare paths.
            for doc in base_docs:
                pod.podcache.document_cache.remove(doc)
                pod.podcache.collection_cache.remove_document_locales(doc)

            # Force load the docs and fix locales.
            docs_loader.DocsLoader.load(pod, base_docs, ignore_errors=True)
            docs_loader.DocsLoader.fix_default_locale(
                pod, base_docs, ignore_errors=True)

            # The routing map should remain unchanged most of the time.
            added_docs = []
            removed_docs = []
            for original_doc in original_docs:
                # Removed documents should be removed.
                if not original_doc.exists:
                    removed_docs.append(original_doc)
                    continue

                updated_doc = pod.get_doc(
                    original_doc.pod_path, original_doc._locale_kwarg)

                # When the serving path has changed, updated in routes.
                if (updated_doc.has_serving_path()
                        and original_doc.get_serving_path() != updated_doc.get_serving_path()):
                    added_docs.append(updated_doc)
                    removed_docs.append(original_doc)

                # If the locales change then we need to adjust the routes.
                original_locales = set([str(l) for l in original_doc.locales])
                updated_locales = set([str(l) for l in updated_doc.locales])

                new_locales = updated_locales - original_locales
                for locale in new_locales:
                    new_doc = pod.get_doc(original_doc.pod_path, locale)
                    if new_doc.has_serving_path() and new_doc not in added_docs:
                        added_docs.append(new_doc)

                removed_locales = original_locales - updated_locales
                for locale in removed_locales:
                    removed_doc = pod.get_doc(original_doc.pod_path, locale)
                    if removed_doc.has_serving_path():
                        if removed_doc not in removed_docs:
                            removed_docs.append(removed_doc)

            # Check for new docs.
            for trigger_doc in trigger_docs:
                if trigger_doc.has_serving_path():
                    if not pod.router.routes.match(trigger_doc.get_serving_path()):
                        added_docs.append(trigger_doc)
            if added_docs or removed_docs:
                pod.router.reconcile_documents(
                    remove_docs=removed_docs, add_docs=added_docs)

        if previous_result:
            return previous_result
        return None


# pylint: disable=abstract-method
class RoutesExtension(extensions.BaseExtension):
    """Extension for handling core routes functionality."""

    @property
    def available_hooks(self):
        """Returns the available hook classes."""
        return [RoutesDevHandlerHook, RoutesDevFileChangeHook]
