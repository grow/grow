"""Threaded loader that forces a list of files to be loaded from filesystem."""

from grow.common import utils as common_utils
from grow.documents import document_front_matter

if common_utils.is_appengine():
    # pylint: disable=invalid-name
    ThreadPool = None
else:
    from multiprocessing.dummy import Pool as ThreadPool


# pylint: disable=too-few-public-methods
class YamlLoader(object):
    """Loader that threads the file system reads into a cache."""

    MAX_POOL_SIZE = 100
    MIN_POOL_COUNT = 50
    POOL_RATIO = 0.02

    @classmethod
    def load(cls, pod, file_names, ignore_errors=False):
        """Load the files from file system."""
        if not file_names:
            return

        def load_func(file_name):
            """Force the doc to read the source file."""
            _ = pod.read_yaml(file_name)

        with pod.profile.timer('DocsLoader.load'):
            if ThreadPool is None or len(file_names) < cls.MIN_POOL_COUNT:
                for file_name in file_names:
                    load_func(file_name)
                return
            pool_size = min(cls.MAX_POOL_SIZE, len(file_names) * cls.POOL_RATIO)
            pool_size = int(round(pool_size))
            thread_pool = ThreadPool(pool_size)
            results = thread_pool.imap_unordered(load_func, file_names)
            # Loop results to make sure that the threads are all processed.
            for _ in results:
                pass
            thread_pool.close()
            thread_pool.join()
