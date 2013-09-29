from protorpc import messages
from grow.pods import messages as pod_messages
from grow.pods.blueprints import messages as blueprint_messages


class GetDocumentRequest(messages.Message):
  pod = messages.MessageField(pod_messages.PodMessage, 1)
  document = messages.MessageField(blueprint_messages.DocumentMessage, 2)

class GetDocumentResponse(messages.Message):
  document = messages.MessageField(blueprint_messages.DocumentMessage, 1)

class ListBlueprintsRequest(messages.Message):
  pod = messages.MessageField(pod_messages.PodMessage, 1)

class ListBlueprintsResponse(messages.Message):
  blueprints = messages.MessageField(blueprint_messages.BlueprintMessage, 1, repeated=True)

class SearchDocumentsRequest(messages.Message):
  pod = messages.MessageField(pod_messages.PodMessage, 1)
  blueprint = messages.MessageField(blueprint_messages.BlueprintMessage, 2)

class SearchDocumentsResponse(messages.Message):
  documents = messages.MessageField(blueprint_messages.DocumentMessage, 1, repeated=True)
