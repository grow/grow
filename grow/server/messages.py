from protorpc import messages
from grow.pods import messages as pod_messages
from grow.pods.blueprints import messages as blueprint_messages


class OwnerMessage(messages.Message):
  nickname = messages.StringField(1)


class ProjectMessage(messages.Message):
  owner = messages.MessageField(OwnerMessage, 1)
  nickname = messages.StringField(2)


###


class CreateDocumentRequest(messages.Message):
  project = messages.MessageField(ProjectMessage, 1)
  document = messages.MessageField(blueprint_messages.DocumentMessage, 2)


class CreateDocumentResponse(messages.Message):
  document = messages.MessageField(blueprint_messages.DocumentMessage, 1)


class UpdateDocumentRequest(messages.Message):
  project = messages.MessageField(ProjectMessage, 1)
  document = messages.MessageField(blueprint_messages.DocumentMessage, 2)


class UpdateDocumentResponse(messages.Message):
  document = messages.MessageField(blueprint_messages.DocumentMessage, 1)


class GetDocumentRequest(messages.Message):
  pod = messages.MessageField(pod_messages.PodMessage, 1)
  document = messages.MessageField(blueprint_messages.DocumentMessage, 2)


class GetDocumentResponse(messages.Message):
  document = messages.MessageField(blueprint_messages.DocumentMessage, 1)


class ListBlueprintsRequest(messages.Message):
  pod = messages.MessageField(pod_messages.PodMessage, 1)
  project = messages.MessageField(ProjectMessage, 2)


class ListBlueprintsResponse(messages.Message):
  blueprints = messages.MessageField(blueprint_messages.BlueprintMessage, 1, repeated=True)


class SearchDocumentsRequest(messages.Message):
  pod = messages.MessageField(pod_messages.PodMessage, 1)
  blueprint = messages.MessageField(blueprint_messages.BlueprintMessage, 2)


class SearchDocumentsResponse(messages.Message):
  documents = messages.MessageField(blueprint_messages.DocumentMessage, 1, repeated=True)


class CreateExportUrlRequest(messages.Message):
  project = messages.MessageField(ProjectMessage, 1)
  document = messages.MessageField(blueprint_messages.DocumentMessage, 2)


class CreateExportUrlResponse(messages.Message):
  url = messages.StringField(1)


class CreateDownloadUrlRequest(messages.Message):
  project = messages.MessageField(ProjectMessage, 1)
  document = messages.MessageField(blueprint_messages.DocumentMessage, 2)


class CreateDownloadUrlResponse(messages.Message):
  url = messages.StringField(1)


class InitRequest(messages.Message):
  project = messages.MessageField(ProjectMessage, 1)


class InitResponse(messages.Message):
  project = messages.MessageField(ProjectMessage, 1)


class GetFileRequest(messages.Message):
  file = messages.MessageField(pod_messages.FileMessage, 1)


class GetFileResponse(messages.Message):
  file = messages.MessageField(pod_messages.FileMessage, 1)


class UpdateFileRequest(messages.Message):
  file = messages.MessageField(pod_messages.FileMessage, 1)


class UpdateFileResponse(messages.Message):
  file = messages.MessageField(pod_messages.FileMessage, 1)


class ListFilesRequest(messages.Message):
  file_search = messages.MessageField(pod_messages.FileSearchMessage, 1)


class ListFilesResponse(messages.Message):
  files = messages.MessageField(pod_messages.FileMessage, 1, repeated=True)
