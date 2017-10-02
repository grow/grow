"""Threaded loader that forces a list of docs to be loaded from filesystem."""

from grow.common import utils as common_utils

if common_utils.is_appengine():
    # pylint: disable=invalid-name
    pool = None
else:
    from multiprocessing import pool


# pylint: disable=too-few-public-methods
class DocsLoader(object):
    """Loader that threads the docs' file system reads."""

    POOL_SIZE = 50

    @classmethod
    def load(cls, docs):
        """Force load the provided docs to read from file system."""

        def load_func(doc):
            """Force the doc to read the source file."""
            # pylint: disable=pointless-statement
            doc.format.raw_content # raw_content forces file read.

        if pool is None or len(docs) < 10:
            for doc in docs:
                load_func(doc)
            return

        thread_pool = pool.ThreadPool(cls.POOL_SIZE)

        for doc in docs:
            thread_pool.apply_async(load_func, args=(doc))

        thread_pool.close()
        thread_pool.join()
