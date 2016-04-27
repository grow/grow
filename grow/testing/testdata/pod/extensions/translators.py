import grow
from protorpc import messages


class CustomTranslator(grow.Translator):
    KIND = 'custom_translator'

    def _download_content(self, stat):
        content = None
        return stat, content

    def _update_acl(self, stat, locale):
        return

    def _upload_catalog(self, catalog, source_lang):
        return
