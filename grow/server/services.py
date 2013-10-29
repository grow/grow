import os
import httplib
from protorpc import remote
from grow.server import messages
from grow.pods import files
from grow.pods import pods
from grow.pods import commands
from grow import deployments


class ServiceException(remote.ApplicationError):
  def __init__(self, message=None):
    super(ServiceException, self).__init__(
        message, httplib.responses[self.http_status])


class NotFoundException(ServiceException):
  http_status = httplib.NOT_FOUND


class PodService(remote.Service):

  def get_pod_from_request(self, request):
    root = os.path.normpath(os.environ['grow:single_pod_root'])
    return pods.Pod(root)

  def get_document_from_request(self, pod, request):
    return pod.get_document(request.document.doc_path)

  def get_file_from_request(self, pod, request):
    return pod.get_file(request.file.pod_path)

  @remote.method(
      messages.CreateDocumentRequest,
      messages.CreateDocumentResponse)
  def create_document(self, request):
    pod = self.get_pod_from_request(request)
    document = pod.get_document(request.document.doc_path)
    document.create_from_message(request.document)
    message = messages.CreateDocumentResponse()
    message.document = document.to_message()
    return message

  @remote.method(
      messages.ListBlueprintsRequest,
      messages.ListBlueprintsResponse)
  def list_blueprints(self, request):
    pod = self.get_pod_from_request(request)
    results = pod.list_blueprints()
    message = messages.ListBlueprintsResponse()
    message.blueprints = [blueprint.to_message() for blueprint in results]
    return message

  @remote.method(
      messages.SearchDocumentsRequest,
      messages.SearchDocumentsResponse)
  def search_documents(self, request):
    pod = self.get_pod_from_request(request)
    blueprint = pod.get_blueprint(request.blueprint.doc_path)
    docs = blueprint.search_documents()
    message = messages.SearchDocumentsResponse()
    message.documents = [doc.to_message() for doc in docs]
    return message

  @remote.method(
      messages.GetDocumentRequest,
      messages.GetDocumentResponse)
  def get_document(self, request):
    pod = self.get_pod_from_request(request)
    document = self.get_document_from_request(pod, request)
    message = messages.GetDocumentResponse()
    message.document = document.to_message()
    return message

  @remote.method(
      messages.UpdateDocumentRequest,
      messages.UpdateDocumentResponse)
  def update_document(self, request):
    pod = self.get_pod_from_request(request)
    document = pod.get_document(request.document.doc_path)
    document.update_from_message(request.document)
    message = messages.UpdateDocumentResponse()
    message.document = document.to_message()
    return message

  @remote.method(
      messages.CreateDownloadUrlRequest,
      messages.CreateDownloadUrlResponse)
  def create_download_url(self, request):
    pass

  @remote.method(
      messages.CreateExportUrlRequest,
      messages.CreateExportUrlResponse)
  def create_export_url(self, request):
    pod = self.get_pod_from_request(request)
    deployment = deployments.ZipFileDeployment('/edit.grow.io/zips/')
    filename = deployment.deploy(pod)
    message = messages.CreateExportUrlResponse()
    message.url = '/_grow/download/{}'.format(filename)
    return message

  @remote.method(
      messages.InitRequest,
      messages.InitResponse)
  def init(self, request):
    pod = self.get_pod_from_request(request)
    commands.init(pod, None)

  @remote.method(
      messages.GetFileRequest,
      messages.GetFileResponse)
  def get_file(self, request):
    pod = self.get_pod_from_request(request)
    try:
      pod_file = self.get_file_from_request(pod, request)
      message = messages.GetFileResponse()
      message.file = pod_file.to_message()
      return message
    except files.FileDoesNotExistError as e:
      raise NotFoundException(str(e))

  @remote.method(
      messages.UpdateFileRequest,
      messages.UpdateFileResponse)
  def update_file(self, request):
    pod = self.get_pod_from_request(request)
    pod_file = self.get_file_from_request(pod, request)
    pod_file.update_content(request.file.content)
    message = messages.UpdateFileResponse()
    message.file = pod_file.to_message()
    return message

  def delete_file(self, request):
    pass

  @remote.method(
      messages.ListFilesRequest,
      messages.ListFilesResponse)
  def list_files(self, request):
    pod = self.get_pod_from_request(request)
    pod_files = files.File.list(pod, prefix='/')
    message = messages.ListFilesResponse()
    message.files = [pod_file.to_message() for pod_file in pod_files]
    return message
