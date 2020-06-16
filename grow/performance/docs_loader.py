"""Threaded loader that forces a list of docs to be loaded from filesystem."""

import sys
import traceback
from multiprocessing.dummy import Pool as ThreadPool
from grow.common import bulk_errors
from grow.documents import document_front_matter


class Error(Exception):
    """Base loading error."""

    def __init__(self, message):
        super(Error, self).__init__(message)
        self.message = message


class LoadError(Error):
    """Error that occured during the loading."""

    def __init__(self, message, err, err_tb):
        super(LoadError, self).__init__(message)
        self.err = err
        self.err_tb = err_tb


# pylint: disable=too-few-public-methods
class DocsLoader(object):
    """Loader that threads the docs' file system reads."""

    MAX_POOL_SIZE = 100
    MIN_POOL_COUNT = 50
    POOL_RATIO = 0.02

    @staticmethod
    def expand_locales(pod, docs):
        """Expand out the docs list to have the docs for all locales."""
        with pod.profile.timer('DocsLoader.expand_locales'):
            expanded_docs = []
            for doc in docs:
                locales = doc.locales
                if not locales:
                    expanded_docs.append(pod.get_doc(doc.pod_path, None))
                    continue
                for locale in doc.locales:
                    locale_doc = pod.get_doc(doc.pod_path, str(locale))
                    if locale_doc.exists:
                        expanded_docs.append(locale_doc)
                if doc.default_locale not in locales:
                    locale_doc = pod.get_doc(doc.pod_path, doc.default_locale)
                    if locale_doc.exists:
                        expanded_docs.append(locale_doc)
            return expanded_docs

    @staticmethod
    def fix_default_locale(pod, docs, ignore_errors=False):
        """Fixes docs loaded without with the wronge default locale."""
        with pod.profile.timer('DocsLoader.fix_default_locale'):
            root_to_locale = {}
            for doc in docs:
                try:
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
                except document_front_matter.BadFormatError:
                    if not ignore_errors:
                        raise

    @classmethod
    def load(cls, pod, docs, ignore_errors=False, tick=None):
        """Force load the provided docs to read from file system."""
        if not docs:
            return

        def load_func(doc):
            """Force the doc to read the source file."""
            result = LoadResult()
            try:
                # Using doc fields forces file read.
                _ = doc.has_serving_path()
            except document_front_matter.BadFormatError:
                if not ignore_errors:
                    raise
            except Exception as err:  # pylint: disable=broad-except
                _, _, err_tb = sys.exc_info()
                result.errors.append(LoadError(
                    "Error loading {}".format(doc.pod_path),
                    err, err_tb))
            finally:
                if tick:
                    tick()
            return result

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
            errors = []
            for result in results:
                errors = errors + result.errors
            thread_pool.close()
            thread_pool.join()

            if errors:
                text = 'There were {} errors during doc loading.'
                raise bulk_errors.BulkErrors(text.format(len(errors)), errors)

    @classmethod
    def load_from_routes(cls, pod, routes, **kwargs):
        """Force load the docs from the routes."""

        def _doc_from_routes(routes):
            """Generator for docs from the routes."""
            existing_pod_paths = set()
            docs = []

            for _, value, _ in routes.nodes:
                if value.kind != 'doc':
                    continue
                if 'pod_path' in value.meta:
                    pod_path = value.meta['pod_path']
                    if pod_path not in existing_pod_paths:
                        existing_pod_paths.add(pod_path)
                        docs.append(pod.get_doc(pod_path))
            return docs

        cls.load(pod, _doc_from_routes(routes), **kwargs)


class LoadResult(object):
    """Results from a doc loading."""

    def __init__(self):
        self.errors = []
