"""Podcache core extension."""

import os
from grow import extensions
from grow.cache import podcache
from grow.collections import collection
from grow.extensions import hooks
from grow.performance import docs_loader


class PodcacheDevFileChangeHook(hooks.DevFileChangeHook):
    """Handle the dev file change hook."""

    # pylint: disable=arguments-differ
    def trigger(self, previous_result, pod, pod_path, *_args, **_kwargs):
        """Trigger the file change hook."""

        # Remove any raw file in the cache.
        pod.podcache.file_cache.remove(pod_path)

        basename = os.path.basename(pod_path)
        ignore_doc = basename.startswith(collection.Collection.IGNORE_INITIAL)

        if pod_path == '/{}'.format(pod.FILE_PODSPEC):
            pod.podcache.reset()
        elif (pod_path.endswith(collection.Collection.BLUEPRINT_PATH)
              and pod_path.startswith(collection.Collection.CONTENT_PATH)):
            doc = pod.get_doc(pod_path)
            pod.podcache.collection_cache.remove_collection(doc.collection)
        elif pod_path.startswith(collection.Collection.CONTENT_PATH) and not ignore_doc:
            base_docs = []
            for dep_path in pod.podcache.dependency_graph.get_dependents(pod_path):
                base_docs.append(pod.get_doc(dep_path))

            for doc in base_docs:
                pod.podcache.document_cache.remove(doc)
                pod.podcache.collection_cache.remove_document_locales(doc)

            # Force load the docs and fix locales.
            docs_loader.DocsLoader.load(base_docs, ignore_errors=True)
            docs_loader.DocsLoader.fix_default_locale(
                pod, base_docs, ignore_errors=True)
        elif pod_path == '/{}'.format(podcache.FILE_OBJECT_CACHE):
            pod.podcache.update(obj_cache=pod._parse_object_cache_file())
            if pod.podcache.is_dirty:
                pod.logger.info('Object cache changed, updating with new data.')
                pod.podcache.write()

        if previous_result:
            return previous_result
        return None


# pylint: disable=abstract-method
class PodcacheExtension(extensions.BaseExtension):
    """Extension for handling core podcache functionality."""

    @property
    def available_hooks(self):
        """Returns the available hook classes."""
        return [PodcacheDevFileChangeHook]

    def dev_file_change_hook(self):
        """Hook handler for dev file change."""
        return PodcacheDevFileChangeHook(self)
