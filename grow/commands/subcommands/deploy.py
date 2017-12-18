
"""Subcommand for deploying pod."""

import os
import click
from grow.commands import shared
from grow.common import rc_config
from grow.common import utils
from grow.deployments import stats
from grow.deployments.destinations import base
from grow.pods import pods
from grow import storage


CFG = rc_config.RC_CONFIG.prefixed('grow.deploy')


@click.command()
@click.argument('deployment_name', default='default')
@shared.pod_path_argument
@click.option('--confirm/--noconfirm', '-c/-f', default=CFG.get('force', True), is_flag=True,
              help='Whether to confirm prior to deployment.')
@click.option('--test/--notest', default=CFG.get('test', True), is_flag=True,
              help='Whether to run deployment tests.')
@click.option('--test_only', default=False, is_flag=True,
              help='Only run the deployment tests.')
@click.option('--auth',
              help='(deprecated) --auth must now be specified'
                   ' before deploy. Usage: grow --auth=user@example.com deploy')
@shared.force_untranslated_option(CFG)
@shared.preprocess_option(CFG)
@shared.reroute_option(CFG)
@shared.threaded_option(CFG)
@click.pass_context
def deploy(context, deployment_name, pod_path, preprocess, confirm, test,
           test_only, auth, force_untranslated, use_reroute, threaded):
    """Deploys a pod to a destination."""
    if auth:
        text = ('--auth must now be specified before deploy. Usage:'
                ' grow --auth=user@example.com deploy')
        raise click.ClickException(text)
    auth = context.parent.params.get('auth')
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    try:
        pod = pods.Pod(root, storage=storage.FileStorage, use_reroute=use_reroute)
        with pod.profile.timer('grow_deploy'):
            # Always clear the cache when building.
            pod.podcache.reset()
            deployment = pod.get_deployment(deployment_name)
            # use the deployment's environment for preprocessing and later
            # steps.
            if deployment.config.env:
                pod.set_env(deployment.config.env)
            require_translations = pod.podspec.localization.get(
                'require_translations', False)
            require_translations = require_translations and not force_untranslated
            if auth:
                deployment.login(auth)
            if preprocess:
                pod.preprocess()
            if test_only:
                deployment.test()
                return
            content_generator = deployment.dump(pod, use_threading=threaded)
            repo = utils.get_git_repo(pod.root)
            if use_reroute:
                pod.router.use_simple()
                pod.router.add_all()
                paths = pod.router.routes.paths
            else:
                paths, _ = pod.determine_paths_to_build()
            stats_obj = stats.Stats(pod, paths=paths)
            deployment.deploy(
                content_generator, stats=stats_obj, repo=repo, confirm=confirm,
                test=test, require_translations=require_translations)
            pod.podcache.write()
    except base.Error as err:
        raise click.ClickException(str(err))
    except pods.Error as err:
        raise click.ClickException(str(err))
    return pod
