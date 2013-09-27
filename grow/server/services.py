import os
from protorpc import remote
from grow.server import messages
from grow.pods import pods


class PodService(remote.Service):

  @remote.method(
      messages.ListBlueprintsRequest,
      messages.ListBlueprintsResponse)
  def list_blueprints(self, request):
    pod = get_pod_from_request(request)
    results = pod.list_blueprints()
    message = messages.ListBlueprintsResponse()
    message.blueprints = [blueprint.to_message() for blueprint in results]
    return message


def get_pod_from_request(request):
  root = os.path.normpath(os.environ['grow:single_pod_root'])
  return pods.Pod(root)
