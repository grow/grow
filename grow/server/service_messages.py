from protorpc import messages
from protorpc import message_types
from grow.pods import messages as pod_messages
from grow.pods.content import messages as content_messages
from grow.pods.controllers import messages as controller_messages


class ListPodsRequest(messages.Message):
  pass


class ListPodsResponse(messages.Message):
  pod_names = messages.StringField(1, repeated=True)


class FinalizeStagedFilesRequest(messages.Message):
  pod = messages.MessageField(pod_messages.PodMessage, 1)


class PodFileResponse(messages.Message):
  pod_name = messages.StringField(1)
  changeset = messages.StringField(2)
  pod_path = messages.StringField(3)
  full_path = messages.StringField(4)
  content_url = messages.StringField(5)


class LaunchPodRequest(messages.Message):
  pod = messages.MessageField(pod_messages.PodMessage, 1)
  ttl = message_types.DateTimeField(2)


class LaunchPodResponse(messages.Message):
  new_pod = messages.MessageField(pod_messages.PodMessage, 1)
  old_pod = messages.MessageField(pod_messages.PodMessage, 2)
  ttl = message_types.DateTimeField(3)


class TakedownPodRequest(messages.Message):
  pod = messages.MessageField(pod_messages.PodMessage, 1)
  ttl = message_types.DateTimeField(3)


class TakedownPodResponse(messages.Message):
  pod = messages.MessageField(pod_messages.PodMessage, 1)


class ListFilesInPodRequest(messages.Message):
  pod = messages.MessageField(pod_messages.PodMessage, 1)


class UploadUrlMessage(messages.Message):
  pod = messages.MessageField(pod_messages.PodMessage, 1)
  pod_path = messages.StringField(2)


class SignedUploadUrlMessage(messages.Message):
  url = messages.StringField(1)
  policy = messages.StringField(2)
  signature = messages.StringField(3)
  google_access_id = messages.StringField(4)
  bucket = messages.StringField(5)
  pod_path = messages.StringField(6)
  filename = messages.StringField(7)
  access_token = messages.StringField(8)


class GetUploadUrlRequest(messages.Message):
  upload_urls = messages.MessageField(UploadUrlMessage, 1, repeated=True)


class GetUploadUrlResponse(messages.Message):
  signed_upload_urls = messages.MessageField(SignedUploadUrlMessage, 1,
                                             repeated=True)


class PodChangesetMessage(messages.Message):
  pod = messages.MessageField(pod_messages.PodMessage, 1)
  launched = message_types.DateTimeField(2)
  launched_by = messages.StringField(3)
  staged = message_types.DateTimeField(4)
  staged_by = messages.StringField(5)


class ListLivePodsRequest(messages.Message):
  pass


class ListLivePodsResponse(messages.Message):
  live_pods = messages.MessageField(PodChangesetMessage, 1, repeated=True)


class GetPodRequest(messages.Message):
  pod = messages.MessageField(pod_messages.PodMessage, 1)


class GetPodResponse(messages.Message):
  pod = messages.MessageField(pod_messages.PodMessage, 1)


class ListChangesetsForPodRequest(messages.Message):
  pod_name = messages.StringField(1)


class ListChangesetsForPodResponse(messages.Message):
  pod_name = messages.StringField(1)
  staged_pods = messages.MessageField(PodChangesetMessage, 2, repeated=True)


class GetTranslationRequest(messages.Message):
  pod = messages.MessageField(pod_messages.PodMessage, 1)
  locales = messages.StringField(2, repeated=True)


class GetTranslationResponse(messages.Message):
  translations = messages.MessageField(
      pod_messages.TranslationMessage, 1, repeated=True)


class GetControllerRequest(messages.Message):
  pod = messages.MessageField(pod_messages.PodMessage, 1)
  controller = messages.MessageField(controller_messages.ControllerMessage, 2)


class GetControllerResponse(messages.Message):
  pod = messages.MessageField(pod_messages.PodMessage, 1)
  controller = messages.MessageField(controller_messages.ControllerMessage, 2)


class GetContentTemplateRequest(messages.Message):
  pod = messages.MessageField(pod_messages.PodMessage, 1)
  content_template = messages.MessageField(content_messages.TemplateMessage, 2)


class GetContentTemplateResponse(messages.Message):
  content_template = messages.MessageField(content_messages.TemplateMessage, 1) 


class ListDocumentsRequest(messages.Message):
  pod = messages.MessageField(pod_messages.PodMessage, 1)


class ListDocumentsResponse(messages.Message):
  documents = messages.MessageField(content_messages.DocumentsMessage, 1)


class GetDocumentRequest(messages.Message):
  pod = messages.MessageField(pod_messages.PodMessage, 1)
  path = messages.StringField(2)


class GetDocumentResponse(messages.Message):
  document = messages.MessageField(content_messages.DocumentMessage, 1)


class ListContentTemplatesRequest(messages.Message):
  pod = messages.MessageField(pod_messages.PodMessage, 1)


class ListContentTemplatesResponse(messages.Message):
  content_templates = messages.MessageField(content_messages.TemplateMessage, 1,
                                            repeated=True)


class DeployPodRequest(messages.Message):
  pod = messages.MessageField(pod_messages.PodMessage, 1)


class DeployPodResponse(messages.Message):
  pod = messages.MessageField(pod_messages.PodMessage, 1)


class WriteFileRequest(messages.Message):
  pod = messages.MessageField(pod_messages.PodMessage, 1)
  file_transfer = messages.MessageField(pod_messages.FileTransferMessage, 2)


class WriteFileResponse(messages.Message):
  pass
