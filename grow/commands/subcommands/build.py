"""Command for building pods into static deployments."""

import os
import click
from grow.commands import shared
from grow.common import bulk_errors
from grow.common import rc_config
from grow.common import utils
from grow.deployments import stats
from grow.deployments.destinations import local as local_destination
from grow.extensions import hooks
from grow.performance import docs_loader
from grow.pods import pods
from grow.rendering import renderer
from grow import storage


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
@shared.threaded_option(CFG)
@shared.shards_option
@shared.shard_option
@shared.work_dir_option
@shared.routes_file_option()
def build(pod_path, out_dir, preprocess, clear_cache, pod_paths,
          locate_untranslated, deployment, threaded, locale, shards, shard,
          work_dir, routes_file):
    """Generates static files and dumps them to a local destination."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    out_dir = out_dir or os.path.join(root, 'build')

    pod = pods.Pod(root, storage=storage.FileStorage)
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
            pod.router.use_simple()
            is_partial = bool(pod_paths) or bool(locale)
            if pod_paths:
                pod_paths = [pod.clean_pod_path(path) for path in pod_paths]
                pod.router.add_pod_paths(pod_paths)
            elif routes_file:
                pod.router.from_data(pod.read_json(routes_file))
            else:
                pod.router.add_all()
            if locale:
                pod.router.filter('whitelist', locales=list(locale))

            # Shard the routes when using sharding.
            if shards and shard:
                is_partial = True
                pod.router.shard(shards, shard)

            if not work_dir:
                # Preload the documents used by the paths after filtering.
                docs_loader.DocsLoader.load_from_routes(pod, pod.router.routes)

            paths = pod.router.routes.paths
            content_generator = renderer.Renderer.rendered_docs(
                pod, pod.router.routes, source_dir=work_dir,
                use_threading=threaded)
            content_generator = hooks.generator_wrapper(
                pod, 'pre_deploy', content_generator, 'build')
            stats_obj = stats.Stats(pod, paths=paths)
            destination.deploy(
                content_generator, stats=stats_obj, repo=repo, confirm=False,
                test=False, is_partial=is_partial)
            pod.podcache.write()
    except bulk_errors.BulkErrors as err:
        # Write the podcache files even when there are rendering errors.
        pod.podcache.write()
        bulk_errors.display_bulk_errors(err)
        raise click.Abort()
    except pods.Error as err:
        raise click.ClickException(str(err))
    if locate_untranslated:
        pod.translation_stats.pretty_print()
        destination.export_untranslated_catalogs()
    return pod
