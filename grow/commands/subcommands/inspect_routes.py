"""Subcommand for displaying all routes of a pod."""

import json
import os

import click

from grow import storage
from grow.commands import shared
from grow.common import rc_config
from grow.pods import pods

CFG = rc_config.RC_CONFIG.prefixed('grow.routes')


@click.command(name='routes')
@shared.deployment_option(CFG)
@shared.routes_file_option('Export route information to a json file.')
@shared.pod_path_argument
def inspect_routes(pod_path, routes_file, deployment):
    """Lists routes handled by a pod."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage)
    if deployment:
        deployment_obj = pod.get_deployment(deployment)
        pod.set_env(deployment_obj.config.env)
    with pod.profile.timer('grow_inspect_routes'):
        out = []
        pod.router.use_simple()
        pod.router.add_all()

        if routes_file:
            # print pod.router.routes.export()
            pod.write_file(
                routes_file,
                json.dumps(
                    pod.router.routes.export(), sort_keys=True, indent=2,
                    separators=(',', ': ')))
            print(f'Exported routes to file: {routes_file}')
            return pod

        for path, node, _ in pod.router.routes.nodes:
            out.append(f'{path} [{node.kind}]\n    {node.meta}\n')
        click.echo_via_pager('\n'.join(out))
    return pod
