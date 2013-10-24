import os
from protorpc import remote
from grow.server import messages
from grow.pods import pods


class PodService(remote.Service):

  def get_pod_from_request(self, request):
    root = os.path.normpath(os.environ['grow:single_pod_root'])
    return pods.Pod(root)

  def get_document_from_request(self, pod, request):
    return pod.get_document(request.document.pod_path)

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
    blueprint = pod.get_blueprint(request.blueprint.nickname)
    docs = blueprint.search()
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
