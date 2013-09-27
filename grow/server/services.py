from protorpc import remote
from grow.server import messages


class PodService(remote.Service):

  @remote.method(
      messages.ListBlueprintsRequest,
      messages.ListBlueprintsResponse)
  def list_blueprints(self, request):
    message = messages.ListBlueprintsResponse()
    message.content = 'foo'
    return message
