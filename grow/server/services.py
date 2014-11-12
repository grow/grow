import datetime
import json
import base64
import logging
import os
import httplib
from protorpc import remote
from grow.common import config
from grow.server import messages
from grow.pods.collectionz import collectionz
from grow.pods.collectionz import documents
from grow.pods import files
from grow.pods import pods
from grow.pods import commands


class ServiceException(remote.ApplicationError):
  http_status = httplib.BAD_REQUEST

  def __init__(self, message=None):
    super(ServiceException, self).__init__(
        message, httplib.responses[self.http_status])


class NotFoundException(ServiceException):
  http_status = httplib.NOT_FOUND


class PodService(remote.Service):

  def get_pod_from_request(self, request):
    root = os.path.normpath(os.environ['grow:single_pod_root'])
    return pods.Pod(root)

  def get_doc_from_request(self, pod, request):
    try:
      return pod.get_doc(request.document.pod_path)
    except documents.Error as e:
      raise ServiceException(str(e))

  def get_file_from_request(self, pod, request):
    return pod.get_file(request.file.pod_path)

  @remote.method(
      messages.CreateCollectionRequest,
      messages.CreateCollectionResponse)
  def create_collection(self, request):
    pod = self.get_pod_from_request(request)
    try:
      collection = pod.get_collection(request.collection.collection_path)
      collection.create_from_message(request.collection)
    except collectionz.Error as e:
      logging.exception(e)
      raise ServiceException(str(e))
    message = messages.CreateCollectionResponse()
    message.collection = collection.to_message()
    return message

  @remote.method(
      messages.DeleteCollectionRequest,
      messages.DeleteCollectionResponse)
  def delete_collection(self, request):
    pod = self.get_pod_from_request(request)
    try:
      collection = pod.get_collection(request.collection.collection_path)
      collection.delete()
      message = messages.DeleteCollectionResponse()
      return message
    except Exception as e:
      raise ServiceException(str(e))

  @remote.method(
      messages.CreateDocumentRequest,
      messages.CreateDocumentResponse)
  def create_document(self, request):
    pod = self.get_pod_from_request(request)
    try:
      document = pod.get_doc(request.document.doc_path)
      document.create_from_message(request.document)
    except Exception as e:
      logging.exception(e)
      raise ServiceException(str(e))
    message = messages.CreateDocumentResponse()
    message.document = document.to_message()
    return message

  @remote.method(
      messages.ListCollectionsRequest,
      messages.ListCollectionsResponse)
  def list_collections(self, request):
    pod = self.get_pod_from_request(request)
    try:
      results = pod.list_collections()
      message = messages.ListCollectionsResponse()
      message.collections = [collection.to_message() for collection in results]
      return message
    except Exception as e:
      logging.exception(e)
      raise ServiceException(str(e))

  @remote.method(
      messages.SearchDocumentsRequest,
      messages.SearchDocumentsResponse)
  def search_documents(self, request):
    pod = self.get_pod_from_request(request)
    try:
      collection = pod.get_collection(request.collection.collection_path)
      docs = collection.search_documents()
    except collectionz.CollectionDoesNotExistError as e:
      raise NotFoundException(str(e))
    except Exception as e:
      logging.exception(e)
      raise ServiceException(str(e))
    message = messages.SearchDocumentsResponse()
    message.documents = [doc.to_message() for doc in docs]
    return message

  @remote.method(
      messages.GetDocumentRequest,
      messages.GetDocumentResponse)
  def get_document(self, request):
    pod = self.get_pod_from_request(request)
    document = self.get_doc_from_request(pod, request)
    if not document.exists():
      raise NotFoundException('{} does not exist.'.format(document))
    message = messages.GetDocumentResponse()
    message.document = document.to_message()
    return message

  @remote.method(
      messages.UpdateDocumentRequest,
      messages.UpdateDocumentResponse)
  def update_document(self, request):
    pod = self.get_pod_from_request(request)
    try:
      document = pod.get_document(request.document.doc_path)
      document.update_from_message(request.document)
    except Exception as e:
      logging.exception(e)
      raise ServiceException(str(e))
    message = messages.UpdateDocumentResponse()
    message.document = document.to_message()
    return message

  @remote.method(
      messages.DeleteDocumentRequest,
      messages.DeleteDocumentResponse)
  def delete_document(self, request):
    pod = self.get_pod_from_request(request)
    document = self.get_doc_from_request(pod, request)
    document.delete()
    message = messages.DeleteDocumentResponse()
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
    content = (request.file.content_b64
               if request.file.content_b64 else request.file.content)
    try:
      pod_file = self.get_file_from_request(pod, request)
      pod_file.update_content(content)
    except files.FileDoesNotExistError:
      pod_file = pod.create_file(request.file.pod_path, content)
    message = messages.UpdateFileResponse()
    message.file = pod_file.to_message()
    return message

  @remote.method(
      messages.MoveFileRequest,
      messages.MoveFileResponse)
  def move_file(self, request):
    pod = self.get_pod_from_request(request)
    pod_file = pod.get_file(request.source_file.pod_path)
    pod_file.move_to(request.destination_file.pod_path)
    message = messages.MoveFileResponse()
    message.file = pod_file.to_message()
    return message

  @remote.method(
      messages.DeleteFileRequest,
      messages.DeleteFileResponse)
  def delete_file(self, request):
    pod = self.get_pod_from_request(request)
    pod_file = self.get_file_from_request(pod, request)
    pod_file.delete()
    message = messages.DeleteFileResponse()
    return message

  @remote.method(
      messages.GetLocalesRequest,
      messages.GetLocalesResponse)
  def get_locales(self, request):
    pod = self.get_pod_from_request(request)
    message = messages.GetLocalesResponse()
    message.locales = pod.locales.to_message()
    return message

  @remote.method(
      messages.GetCatalogRequest,
      messages.GetCatalogResponse)
  def get_catalog(self, request):
    pod = self.get_pod_from_request(request)
    catalog = pod.catalogs.get(request.catalog.locale)
    message = messages.GetCatalogResponse()
    message.catalog = catalog.to_message()
    return message

  @remote.method(
      messages.ExtractRequest,
      messages.ExtractResponse)
  def extract_translations(self, request):
    pod = self.get_pod_from_request(request)
    pod.catalogs.extract()
    message = messages.ExtractResponse()
    return message

  @remote.method(
      messages.ListFilesRequest,
      messages.ListFilesResponse)
  def list_files(self, request):
    pod = self.get_pod_from_request(request)
    pod_files = files.File.list(pod, prefix='/')
    message = messages.ListFilesResponse()
    message.files = [pod_file.to_message() for pod_file in pod_files]
    return message

  @remote.method(
      messages.GetRoutesRequest,
      messages.GetRoutesResponse)
  def get_routes(self, request):
    pod = self.get_pod_from_request(request)
    message = messages.GetRoutesResponse()
    try:
      routes = pod.get_routes()
      message.routes = routes.to_message()
    except Exception as e:
      logging.exception(e)
      raise ServiceException(str(e))
    return message

  @remote.method(
      messages.GetFileUploadUrlRequest,
      messages.GetFileUploadUrlResponse)
  def get_file_upload_url(self, request):
    signed_upload_urls = []
    google_access_id = config.get_google_access_id()
#    access_token, _ = app_identity.get_access_token(SCOPE)
    for upload_url_message in request.upload_urls:
      filename = 'pods/{}{}'.format(
          upload_url_message.pod.changeset,
          upload_url_message.pod_path)
      expires = '%sZ' % (datetime.datetime.utcnow()
                         + datetime.timedelta(hours=1)).isoformat()[:19]
      policy = base64.b64encode(json.dumps({
          'expiration': expires,
          'conditions': [
              ['eq', '$bucket', config.BUCKET],
              ['eq', '$key', filename],
#              ['eq', '$x-goog-meta-owner', 'jeremydw@gmail.com'],
          ],
      }))
      signature = base64.b64encode(config.sign_blob(policy))
      signed_upload_url_message = messages.SignedUploadUrlMessage()
      signed_upload_url_message.url = config.GCS_API_URL
      signed_upload_url_message.bucket = config.BUCKET
      signed_upload_url_message.policy = policy
      signed_upload_url_message.signature = signature
      signed_upload_url_message.google_access_id = google_access_id
      signed_upload_url_message.filename = filename
      signed_upload_url_message.pod_path = upload_url_message.pod_path
#      signed_upload_url_message.access_token = access_token
      signed_upload_urls.append(signed_upload_url_message)
    message = messages.GetUploadUrlResponse()
    message.signed_upload_urls = signed_upload_urls
    return message
