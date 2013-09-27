from protorpc import messages
from grow.pods import messages as pod_messages
from grow.pods.blueprints import messages as blueprint_messages


class ListBlueprintsRequest(messages.Message):
  pod = messages.MessageField(pod_messages.PodMessage, 1)


class ListBlueprintsResponse(messages.Message):
  blueprints = messages.MessageField(blueprint_messages.BlueprintMessage, 1, repeated=True)
