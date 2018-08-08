"""Pod configuration specification."""

from grow.cache import locale_alias_cache
from grow.common import structures


class PodSpec(structures.DeepReferenceDict):
    """Grow pod specification configuration."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.locale_aliases = locale_alias_cache.LocaleAliasCache()
        self.locale_aliases.add_all(self['localization.aliases'] or {})
