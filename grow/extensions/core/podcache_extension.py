"""Podcache core extension."""

from grow import extensions
from grow.cache import podcache
from grow.collections import collection
from grow.extensions import hooks


class PodcacheDevFileChangeHook(hooks.DevFileChangeHook):
    """Handle the dev file change hook."""

    # pylint: disable=arguments-differ
    def trigger(self, previous_result, pod_path, *_args, **kwargs):
        """Trigger the file change hook."""

        # We don't want to write cache files when just serving.
        write_cache_file = True
        if 'write_cache_file' in kwargs:
            write_cache_file = kwargs['write_cache_file']

        # Remove any raw file in the cache.
        self.pod.podcache.file_cache.remove(pod_path)

        if pod_path == '/{}'.format(self.pod.FILE_PODSPEC):
            self.pod.podcache.reset()
        elif (pod_path.endswith(collection.Collection.BLUEPRINT_PATH)
              and pod_path.startswith(collection.Collection.CONTENT_PATH)):
            doc = self.pod.get_doc(pod_path)
            self.pod.podcache.collection_cache.remove_collection(doc.collection)
        elif pod_path == '/{}'.format(podcache.FILE_OBJECT_CACHE):
            self.pod.podcache.update(obj_cache=self.pod._parse_object_cache_file())
            if write_cache_file and self.pod.podcache.is_dirty:
                self.pod.logger.info('Object cache changed, updating with new data.')
                self.pod.podcache.write()
        else:
            # Clear any documents that depend on the pod_path.
            for dep_path in self.pod.podcache.dependency_graph.get_dependents(pod_path):
                doc = self.pod.get_doc(dep_path)
                self.pod.podcache.document_cache.remove(doc)
                self.pod.podcache.collection_cache.remove_document_locales(doc)

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
