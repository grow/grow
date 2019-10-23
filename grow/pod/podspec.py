"""Pod configuration specification."""

from grow.cache import locale_alias_cache
from grow.common import structures
from grow.data import untag


POD_SPEC_FILE = 'podspec.yaml'


class PodSpec(object):
    """Grow pod specification configuration."""

    def __getitem__(self, key):
        """Ability to reference the parsed object."""
        return self.parsed[key]

    def __init__(self, tagged_data):
        # Store the tagged data to be untagged when environment changes.
        self.tagged_data = tagged_data
        self.locale_aliases = locale_alias_cache.LocaleAliasCache()
        self.parsed = structures.DeepReferenceDict()

        # Start without any environment set.
        self.update_env()

        # Cache the localization aliases.
        try:
            self.locale_aliases.add_all(self['localization.aliases'] or {})
        except KeyError:
            pass

    def update_env(self, env=None):
        """Update the parsed yaml based on the environment."""
        self.parsed = structures.DeepReferenceDict(
            untag.Untag.untag(self.tagged_data, params={
                'env': untag.UntagParamRegex(env) if env else None,
            }))
