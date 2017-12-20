"""Command for building pods into static deployments."""

import os
import click
from grow.commands import shared
from grow.common import rc_config
from grow.common import utils
from grow.deployments import stats
from grow.deployments.destinations import local as local_destination
from grow.pods import pods
from grow import storage
from grow.rendering import renderer


CFG = rc_config.RC_CONFIG.prefixed('grow.build')


# pylint: disable=too-many-locals
@click.command()
@shared.pod_path_argument
@click.option('--clear-cache',
              default=CFG.get('clear-cache', False), is_flag=True,
              help='Clear the pod cache before building.')
@click.option('--file', '--pod-path', 'pod_paths',
              help='Build only pages affected by content files.', multiple=True)
@click.option('--locate-untranslated',
              default=CFG.get('locate-untranslated', False), is_flag=True,
              help='Shows untranslated message information.')
@shared.locale_option(help_text='Filter build routes to specific locale.')
@shared.deployment_option(CFG)
@shared.out_dir_option(CFG)
@shared.preprocess_option(CFG)
@shared.reroute_option(CFG)
@shared.threaded_option(CFG)
def build(pod_path, out_dir, preprocess, clear_cache, pod_paths,
          locate_untranslated, deployment, use_reroute, threaded, locale):
    """Generates static files and dumps them to a local destination."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    out_dir = out_dir or os.path.join(root, 'build')

    pod = pods.Pod(root, storage=storage.FileStorage, use_reroute=use_reroute)
    if not pod_paths or clear_cache:
        # Clear the cache when building all, only force if the flag is used.
        pod.podcache.reset(force=clear_cache)
    deployment_obj = None
    if deployment:
        deployment_obj = pod.get_deployment(deployment)
        pod.set_env(deployment_obj.config.env)
    if preprocess:
        with pod.profile.timer('grow_preprocess'):
            pod.preprocess()
    if locate_untranslated:
        pod.enable(pod.FEATURE_TRANSLATION_STATS)
    try:
        with pod.profile.timer('grow_build'):
            config = local_destination.Config(out_dir=out_dir)
            # When using a specific deployment env need to also copy over.
            if deployment_obj:
                config.env = deployment_obj.config.env
            destination = local_destination.LocalDestination(config)
            destination.pod = pod
            repo = utils.get_git_repo(pod.root)
            if use_reroute:
                pod.router.use_simple()
                if pod_paths:
                    pod.router.add_pod_paths(pod_paths)
                else:
                    pod.router.add_all()
                if locale:
                    pod.router.filter(locales=list(locale))
                paths = pod.router.routes.paths
                content_generator = renderer.Renderer.rendered_docs(
                    pod, pod.router.routes, use_threading=threaded)
            else:
                paths, _ = pod.determine_paths_to_build(pod_paths=pod_paths)
                content_generator = destination.dump(
                    pod, pod_paths=pod_paths, use_threading=threaded)
            stats_obj = stats.Stats(pod, paths=paths)
            is_partial = bool(pod_paths) or bool(locale)
            destination.deploy(
                content_generator, stats=stats_obj, repo=repo, confirm=False,
                test=False, is_partial=is_partial)

            pod.podcache.write()
    except pods.Error as err:
        raise click.ClickException(str(err))
    if locate_untranslated:
        pod.translation_stats.pretty_print()
        destination.export_untranslated_catalogs()
    return pod
