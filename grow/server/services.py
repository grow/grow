"""

/_ah/api/discovery/v1/apis
/_ah/api/explorer

"""

from google.appengine.ext import endpoints
from growspace import services as api
from grow.common import config
from grow.pods import deployment
from grow.pods import messages as pod_messages
from grow.pods import pods
from grow.pods import service_messages as messages
from grow.pods.controllers import messages as controller_messages
from protorpc import remote
import base64
import datetime
import json

SCOPE = 'https://www.googleapis.com/auth/devstorage.full_control'


@api.api_class(resource_name='pods')
class PodService(remote.Service):


  @endpoints.method(
      messages.GetPodRequest, messages.GetPodResponse,
      path='pod', http_method='GET')
  def get(self, request):
    pod = _get_pod_from_request_or_die(request)
    message = messages.GetPodResponse()
    message.pod = pod.to_message()
    return message

  @endpoints.method(
      messages.ListChangesetsForPodRequest,
      messages.ListChangesetsForPodResponse,
      name='listChangesetsForPod', path='pods/pod/changesets')
  def list_changesets_for_pod(self, request):
    pod = _get_pod_from_request_or_die(request)
    try:
      changesets = deployment.list_changesets_for_pod(pod.nickname)
    except deployment.PodNotFoundError as e:
      raise endpoints.NotFoundException(str(e))

    message = messages.ListChangesetsForPodResponse()
    message.pod = pod.to_message()
    message.staged_pods = []
    for changeset, data in changesets.iteritems():
      changeset_message = messages.PodChangesetMessage()
      changeset_message.staged = data.get('staged')
      changeset_message.staged_by = data.get('staged_by')
      changeset_message.changeset = changeset
      message.staged_pods.append(changeset_message)
    return message

  @endpoints.method(
      messages.DeployPodRequest, messages.DeployPodResponse,
      name='deploy', path='pods/deploy')
  def deploy(self, request):
    pod = _get_pod_from_request_or_die(request)
    pod.deploy()
    message = messages.DeployPodResponse()
    return message

  @endpoints.method(
      messages.LaunchPodRequest, messages.LaunchPodResponse,
      name='launch', path='pods/launch')
  def launch(self, request):
    pod = _get_pod_from_request_or_die(request)
    try:
      user = endpoints.get_current_user()
      email = user.email() if user else None
      _, old_pod, _ = deployment.launch(pod, request.ttl, user=email)
    except deployment.AlreadyLaunchedError as e:
      raise endpoints.BadRequestException(str(e))
    except deployment.PodNotFoundError as e:
      raise endpoints.NotFoundException(str(e))

    message = messages.LaunchPodResponse()
    message.new_pod = pod.to_message()
    message.old_pod = old_pod.to_message()
    return message

  @endpoints.method(
      messages.ListPodsRequest, messages.ListPodsResponse,
      name='list')
  def list(self, request):
    pod_names = deployment.list_staged_pods()
    message = messages.ListPodsResponse()
    message.pod_names = pod_names
    return message

  @endpoints.method(
      messages.ListLivePodsRequest, messages.ListLivePodsResponse,
      name='listLivePods', path='pods/listLivePods')
  def list_live_pods(self, request):
    try:
      live_pods = deployment.get_live_pods()
    except deployment.LiveRoutingMapNotFound as e:
      raise endpoints.NotFoundException(str(e))
    message = messages.ListLivePodsResponse()
    message.live_pods = []
    for pod_name, data in live_pods.pod_names_to_data.iteritems():
      pod_message = messages.PodChangesetMessage()
      pod_message.pod_name = pod_name
      pod_message.changeset = data['changeset']
      pod_message.launched = data.get('launched')
      pod_message.launched_by = data.get('launched_by')
      message.live_pods.append(pod_message)
    return message

  @endpoints.method(
      messages.ListFilesInPodRequest, pod_messages.PodFilesMessage,
      name='listFilesInPod', path='pods/listFilesInPod')
  def list_files_in_pod(self, request):
    pod = _get_pod_from_request_or_die(request)
    message = pod_messages.PodFilesMessage()
    pod_paths = pod.list_files_in_pod()
    for pod_path in pod_paths:
      pod_file_message = pod_messages.PodFileMessage()
      pod_file_message.pod_path = pod_path
      message.pod_files.append(pod_file_message)

  @endpoints.method(
      messages.WriteFileRequest, messages.WriteFileResponse,
      path='pods/file', http_method='POST')
  def write_file(self, request):
    pod = _get_pod_from_request_or_die(request)
    content = base64.b64decode(request.file_transfer.content_b64)
    pod.write_file(request.file_transfer.pod_path, content)
    message = messages.WriteFileResponse()
    return message

  @endpoints.method(
      messages.GetUploadUrlRequest, messages.GetUploadUrlResponse,
      name='getUploadUrl', path='pods/getUploadUrl')
  def get_upload_url(self, request):
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

  @endpoints.method(
      messages.FinalizeStagedFilesRequest, messages.PodFileResponse,
      name='finalizeStagedFiles', path='pods/finalizeStagedFiles')
  def finalize_staged_files(self, request):
    pod = _get_pod_from_request_or_die(request)
    deployment.finalize_staged_files(pod, user=endpoints.get_current_user())
    message = messages.PodFileResponse()
#    message.pod_name = pod.nickname
#    message.changeset = request.changeset
#    message.pod_path = request.pod_path
#    message.full_path = full_path
    return message

  @endpoints.method(
      messages.TakedownPodRequest, messages.TakedownPodResponse,
      name='takedown', path='pods/takedown')
  def takedown(self, request):
    pod = _get_pod_from_request_or_die(request)
    try:
      deployment.takedown(pod, request.ttl)
    except deployment.PodNotLiveError as e:
      raise endpoints.NotFoundException(str(e))
    message = messages.TakedownPodResponse()
    message.pod = pod.to_message()
    return message

  @endpoints.method(
      messages.GetTranslationRequest, messages.GetTranslationResponse,
      name='translation', path='pods/translation')
  def get_translation(self, request):
    pod = _get_pod_from_request_or_die(request)

    if request.locales is None:
      locales = pod.translations.list_locales()
    else:
      locales = request.locales

    message = messages.GetTranslationResponse()
    message.translations = []
    for locale in locales:
      translation = pod.translations.get_translation(locale)
      message.translations.append(translation.to_message())
    return message

  @endpoints.method(
      messages.GetControllerRequest, messages.GetControllerResponse,
      name='controller', path='pods/controllers')
  def get_controller(self, request):
    pod = _get_pod_from_request_or_die(request)
    page = pod.get_resource_by_id(request.controller.page.key)
    if not page:
      message = 'Controller {} not found in {}@{}.'.format(
          request.controller.page.key, pod.nickname, pod.changeset)
      raise endpoints.NotFoundException(message)
    message = messages.GetControllerResponse()
    message.controller = controller_messages.ControllerMessage()
    # TODO(jeremydw): Handle non-page controllers.
    message.controller.page = page.to_message()
    return message

  @endpoints.method(
      messages.GetContentTemplateRequest, messages.GetContentTemplateResponse,
      name='contentTemplate', path='pods/contentTemplate')
  def get_content_template(self, request):
    pod = _get_pod_from_request_or_die(request)
    content_template = pod.get_content_template_by_id(
        request.content_template.template_id)

    if not content_template:
      message = 'Content template {} not found in {}@{}.'.format(
          request.controller.page.key, pod.nickname, request.changeset)
      raise endpoints.NotFoundException(message)

    message = messages.GetContentTemplateResponse()
    message.content_template = content_template.to_message()
    return message

  @endpoints.method(
      messages.ListContentTemplatesRequest, messages.ListContentTemplatesResponse,
      name='contentTemplates', path='pods/contentTemplates')
  def list_content_templates(self, request):
    pod = _get_pod_from_request_or_die(request)
    template_messages = pod.content_templates.to_message()
    message = messages.ListContentTemplatesResponse()
    message.content_templates = template_messages
    return message

  @endpoints.method(
      messages.ListDocumentsRequest, messages.ListDocumentsResponse,
      name='documents', path='pods/documents')
  def list_documents(self, request):
    pod = _get_pod_from_request_or_die(request)
    message = messages.ListDocumentsResponse()
    message.documents = pod.documents.to_message()
    return message

  @endpoints.method(
      messages.GetDocumentRequest, messages.GetDocumentResponse,
      name='document', path='pods/document')
  def get_document(self, request):
    pod = _get_pod_from_request_or_die(request)
    document = pod.documents.get_by_path(request.path)
    message = messages.GetDocumentResponse()
    message.document = document.to_message()
    return message


def _get_pod_from_request_or_die(request):
  if not request.pod.changeset:
    raise endpoints.BadRequestException('Missing required field: pod.changeset.')
  pod = pods.Pod('{}/{}'.format(config.PODS_DIR, request.pod.changeset))
#  if not pod.exists:
#    message = 'Pod "{}@{}" does not exist.'
#    message = message.format(pod.nickname, request.changeset)
#    raise endpoints.NotFoundException(message)
  return pod
