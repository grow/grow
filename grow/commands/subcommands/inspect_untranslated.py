"""Subcommand for displaying untranslated strings in the pod."""

import os
import click
from grow.commands import shared
from grow.common import rc_config
from grow.pods import pods
from grow import storage
from grow.rendering import renderer


CFG = rc_config.RC_CONFIG.prefixed('grow.inspect.untranslated')


@click.command(name='untranslated')
@shared.pod_path_argument
@shared.locale_option(
    help_text='Which locale(s) to analyze when searching for untranslated strings.')
@shared.localized_option(CFG)
@shared.reroute_option(CFG)
@shared.threaded_option(CFG)
def inspect_untranslated(pod_path, locale, localized, threaded, use_reroute):
    """Displays statistics about the pod."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage, use_reroute=use_reroute)
    with pod.profile.timer('grow_inspect_untranslated'):
        # Find all of the untagged strings.
        catalogs = pod.get_catalogs(template_path=None)
        untagged_strings, _ = catalogs.extract(
            localized=localized, locales=locale, audit=True, out_path=None)

        # Find all the untranslated strings in use.
        pod.enable(pod.FEATURE_TRANSLATION_STATS)
        if use_reroute:
            pod.router.use_simple()
            pod.router.add_all()
            if locale:
                pod.router.filter(locales=list(locale))
            content_generator = renderer.Renderer.rendered_docs(
                pod, pod.router.routes, use_threading=threaded)
        else:
            content_generator = pod.dump(use_threading=threaded)

        # Render each document to get the untranslated strings.
        for _ in content_generator:
            pass

        pod.translation_stats.add_untagged(untagged_strings)
        pod.translation_stats.pretty_print()
    return pod
