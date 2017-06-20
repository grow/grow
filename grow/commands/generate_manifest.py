from grow.pods import pods
from grow.pods import storage
import click
import os
import json


@click.command()
@click.argument('statics_path')
@click.argument('pod_path', default='.')
def generate_manifest(statics_path, pod_path):
    """Generates a g.static manifiest given a pod path."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage)
    try:
        with open('manifest.json', 'w') as f:
            data = {static.pod_path: static.url.path for static in pod.list_statics(statics_path)}
            f.write(json.dumps(data))
    except pods.Error as e:
        raise click.ClickException(str(e))
