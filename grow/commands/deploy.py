from grow.common import utils
from grow.deployments import stats
from grow.deployments.destinations import base
from grow.pods import pods
from grow.pods import storage
import click
import os


@click.command()
@click.argument('deployment_name', required=False, default='default')
@click.argument('pod_path', default='.')
@click.option('--preprocess/--no-preprocess', '-p/-np', default=True,
              is_flag=True, help='Whether to run preprocessors.')
@click.option('--confirm/--noconfirm', '-c/-f', default=True, is_flag=True,
              help='Whether to confirm prior to deployment.')
@click.option('--test/--notest', default=True, is_flag=True,
              help='Whether to run deployment tests.')
@click.option('--test_only', default=False, is_flag=True,
              help='Only run the deployment tests.')
@click.option('--auth',
              help='(deprecated) --auth must now be specified'
                   ' before deploy. Usage: grow --auth=user@example.com deploy')
@click.option('--force-untranslated', 'force_untranslated', default=False, is_flag=True,
              help='Whether to force untranslated strings to be uploaded.')
@click.pass_context
def deploy(context, deployment_name, pod_path, preprocess, confirm, test,
           test_only, auth, force_untranslated):
    """Deploys a pod to a destination."""
    if auth:
        text = ('--auth must now be specified before deploy. Usage:'
                ' grow --auth=user@example.com deploy')
        raise click.ClickException(text)
    auth = context.parent.params.get('auth')
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    try:
        pod = pods.Pod(root, storage=storage.FileStorage)
        with pod.profile.timer('grow_deploy'):
            deployment = pod.get_deployment(deployment_name)
            # use the deployment's environment for preprocessing and later
            # steps.
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
            content_generator = deployment.dump(pod)
            repo = utils.get_git_repo(pod.root)
            paths, _ = pod.determine_paths_to_build()
            stats_obj = stats.Stats(pod, paths=paths)
            deployment.deploy(
                content_generator, stats=stats_obj, repo=repo, confirm=confirm,
                test=test, require_translations=require_translations)
    except base.Error as err:
        raise click.ClickException(str(err))
    except pods.Error as err:
        raise click.ClickException(str(err))
    return pod
