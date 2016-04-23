import logging


class Translator(object):

    def __init__(self, pod, config=None):
        self.pod = pod
        self.config = config or {}

    def upload(self, locales, force=True):
        # TODO: Upload progress and prompt.
        source_lang = self.pod.podspec.default_locale
        locales = locales or self.pod.catalogs.list_locales()
        for locale in locales:
            catalog = self.pod.catalogs.get(locale)
            resp = self._upload_catalog(catalog, source_lang)
