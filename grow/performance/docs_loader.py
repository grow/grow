"""Threaded loader that forces a list of docs to be loaded from filesystem."""

from grow.common import utils as common_utils

if common_utils.is_appengine():
    # pylint: disable=invalid-name
    ThreadPool = None
else:
    from multiprocessing.dummy import Pool as ThreadPool


# pylint: disable=too-few-public-methods
class DocsLoader(object):
    """Loader that threads the docs' file system reads."""

    MAX_POOL_SIZE = 100
    MIN_POOL_COUNT = 50
    POOL_RATIO = 0.02

    @classmethod
    def load(cls, docs):
        """Force load the provided docs to read from file system."""
        if not docs:
            return

        pod = docs[0].pod

        def load_func(doc):
            """Force the doc to read the source file."""
            # pylint: disable=pointless-statement
            doc.has_serving_path()  # Using doc fields forces file read.

        with pod.profile.timer('DocsLoader.load'):
            if ThreadPool is None or len(docs) < cls.MIN_POOL_COUNT:
                for doc in docs:
                    load_func(doc)
                return
            pool_size = min(cls.MAX_POOL_SIZE, len(docs) * cls.POOL_RATIO)
            pool_size = int(round(pool_size))
            thread_pool = ThreadPool(pool_size)
            results = thread_pool.imap_unordered(load_func, docs)
            # Loop results to make sure that the threads are all processed.
            for _ in results:
                pass
            thread_pool.close()
            thread_pool.join()

    @staticmethod
    def expand_locales(pod, docs):
        """Expand out the docs list to have the docs for all locales."""
        with pod.profile.timer('DocsLoader.expand_locales'):
            expanded_docs = []
            for doc in docs:
                for locale in doc.locales:
                    expanded_docs.append(pod.get_doc(doc.pod_path, str(locale)))
            return expanded_docs

    @staticmethod
    def fix_default_locale(pod, docs):
        """Fixes docs loaded without with the wronge default locale."""
        with pod.profile.timer('DocsLoader.fix_default_locale'):
            root_to_locale = {}
            for doc in docs:
                # Ignore the docs that are the same as the default locale.
                kw_locale = doc._locale_kwarg
                if kw_locale is not None:
                    continue
                root_path = doc.root_pod_path
                current_locale = str(doc.locale)
                safe_locale = str(doc.locale_safe)
                if (root_path in root_to_locale
                        and current_locale in root_to_locale[root_path]):
                    continue
                if safe_locale != current_locale:
                    # The None and safe locale is now invalid in the cache
                    # since the front-matter differs.
                    pod.podcache.collection_cache.remove_document_locale(
                        doc, None)
                    pod.podcache.collection_cache.remove_document_locale(
                        doc, doc.locale_safe)

                    # Get the doc for the correct default locale.
                    clean_doc = doc.localize(current_locale)

                    # Cache default locale (based off front-matter).
                    pod.podcache.collection_cache.add_document_locale(
                        clean_doc, None)

                    # If we have already fixed it, ignore any other locales.
                    if root_path not in root_to_locale:
                        root_to_locale[root_path] = []
                    if current_locale not in root_to_locale[root_path]:
                        root_to_locale[root_path].append(current_locale)
