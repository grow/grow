"""Podcache core extension."""

from grow import extensions
from grow.cache import podcache
from grow.collections import collection
from grow.extensions import hooks


class PodcacheDevFileChangeHook(hooks.DevFileChangeHook):
    """Handle the dev file change hook."""

    # pylint: disable=arguments-differ
    def trigger(self, previous_result, pod_path, *_args, **_kwargs):
        """Trigger the file change hook."""

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
            if self.pod.podcache.is_dirty:
                self.pod.logger.info('Object cache changed, updating with new data.')
                self.pod.podcache.write()

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
