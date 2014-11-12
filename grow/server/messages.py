from protorpc import messages
from grow.pods import messages as pod_messages
from grow.pods.collectionz import messages as collection_messages


class OwnerMessage(messages.Message):
  nickname = messages.StringField(1)


class ProjectMessage(messages.Message):
  owner = messages.MessageField(OwnerMessage, 1)
  nickname = messages.StringField(2)
  root = messages.StringField(3)


###


class CreateCollectionRequest(messages.Message):
  project = messages.MessageField(ProjectMessage, 1)
  collection = messages.MessageField(collection_messages.CollectionMessage, 2)


class CreateCollectionResponse(messages.Message):
  collection = messages.MessageField(collection_messages.CollectionMessage, 1)


class DeleteCollectionRequest(messages.Message):
  project = messages.MessageField(ProjectMessage, 1)
  collection = messages.MessageField(collection_messages.CollectionMessage, 2)


class DeleteCollectionResponse(messages.Message):
  pass


class CreateDocumentRequest(messages.Message):
  project = messages.MessageField(ProjectMessage, 1)
  document = messages.MessageField(collection_messages.DocumentMessage, 2)


class CreateDocumentResponse(messages.Message):
  document = messages.MessageField(collection_messages.DocumentMessage, 1)


class UpdateDocumentRequest(messages.Message):
  project = messages.MessageField(ProjectMessage, 1)
  document = messages.MessageField(collection_messages.DocumentMessage, 2)


class UpdateDocumentResponse(messages.Message):
  document = messages.MessageField(collection_messages.DocumentMessage, 1)


class GetDocumentRequest(messages.Message):
  project = messages.MessageField(ProjectMessage, 1)
  document = messages.MessageField(collection_messages.DocumentMessage, 2)


class GetDocumentResponse(messages.Message):
  document = messages.MessageField(collection_messages.DocumentMessage, 1)


class DeleteDocumentRequest(messages.Message):
  project = messages.MessageField(ProjectMessage, 1)
  document = messages.MessageField(collection_messages.DocumentMessage, 2)


class DeleteDocumentResponse(messages.Message):
  pass


class ListCollectionsRequest(messages.Message):
  project = messages.MessageField(ProjectMessage, 1)


class ListCollectionsResponse(messages.Message):
  collections = messages.MessageField(collection_messages.CollectionMessage, 1, repeated=True)


class SearchDocumentsRequest(messages.Message):
  project = messages.MessageField(ProjectMessage, 1)
  collection = messages.MessageField(collection_messages.CollectionMessage, 2)


class SearchDocumentsResponse(messages.Message):
  documents = messages.MessageField(collection_messages.DocumentMessage, 1, repeated=True)


class CreateExportUrlRequest(messages.Message):
  project = messages.MessageField(ProjectMessage, 1)
  document = messages.MessageField(collection_messages.DocumentMessage, 2)


class CreateExportUrlResponse(messages.Message):
  url = messages.StringField(1)


class CreateDownloadUrlRequest(messages.Message):
  project = messages.MessageField(ProjectMessage, 1)
  document = messages.MessageField(collection_messages.DocumentMessage, 2)


class CreateDownloadUrlResponse(messages.Message):
  url = messages.StringField(1)


class InitRequest(messages.Message):
  project = messages.MessageField(ProjectMessage, 1)


class InitResponse(messages.Message):
  project = messages.MessageField(ProjectMessage, 1)


class GetFileRequest(messages.Message):
  project = messages.MessageField(ProjectMessage, 1)
  file = messages.MessageField(pod_messages.FileMessage, 2)


class GetFileResponse(messages.Message):
  file = messages.MessageField(pod_messages.FileMessage, 1)


class UpdateFileRequest(messages.Message):
  project = messages.MessageField(ProjectMessage, 1)
  file = messages.MessageField(pod_messages.FileMessage, 2)


class UpdateFileResponse(messages.Message):
  file = messages.MessageField(pod_messages.FileMessage, 1)


class ListFilesRequest(messages.Message):
  project = messages.MessageField(ProjectMessage, 1)
  file_search = messages.MessageField(pod_messages.FileSearchMessage, 2)


class ListFilesResponse(messages.Message):
  files = messages.MessageField(pod_messages.FileMessage, 1, repeated=True)


class DeleteFileRequest(messages.Message):
  project = messages.MessageField(ProjectMessage, 1)
  file = messages.MessageField(pod_messages.FileMessage, 2)


class DeleteFileResponse(messages.Message):
  pass


class MoveFileRequest(messages.Message):
  project = messages.MessageField(ProjectMessage, 1)
  source_file = messages.MessageField(pod_messages.FileMessage, 2)
  destination_file = messages.MessageField(pod_messages.FileMessage, 3)


class MoveFileResponse(messages.Message):
  file = messages.MessageField(pod_messages.FileMessage, 2)


class GetRoutesRequest(messages.Message):
  project = messages.MessageField(ProjectMessage, 1)


class GetRoutesResponse(messages.Message):
  routes = messages.MessageField(pod_messages.RoutesMessage, 1)


class GetLocalesRequest(messages.Message):
  project = messages.MessageField(ProjectMessage, 1)


class GetLocalesResponse(messages.Message):
  locales = messages.MessageField(pod_messages.LocalesMessage, 1)


class GetCatalogRequest(messages.Message):
  project = messages.MessageField(ProjectMessage, 1)
  catalog = messages.MessageField(pod_messages.CatalogMessage, 2)


class GetCatalogResponse(messages.Message):
  catalog = messages.MessageField(pod_messages.CatalogMessage, 1)


class ExtractRequest(messages.Message):
  project = messages.MessageField(ProjectMessage, 1)


class ExtractResponse(messages.Message):
  catalog = messages.MessageField(pod_messages.CatalogMessage, 1)


###


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


class GetFileUploadUrlRequest(messages.Message):
  upload_urls = messages.MessageField(UploadUrlMessage, 1, repeated=True)


class GetFileUploadUrlResponse(messages.Message):
  signed_upload_urls = messages.MessageField(SignedUploadUrlMessage, 1,
                                             repeated=True)
