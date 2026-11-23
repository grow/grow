"""API Handler for serving editor API requests."""

import datetime
import hashlib
import json
import os
import posixpath

import yaml
from werkzeug import wrappers
from werkzeug.exceptions import BadRequest, NotFound

from grow.common import json_encoder, utils, yaml_utils
from grow.documents import document
from grow.routing import router as grow_router

from .api import screenshot, yaml_conversion


def _validate_pod_path(pod_path):
    """Validates a pod-relative path to prevent directory traversal."""
    if not pod_path or '\x00' in pod_path or '\\' in pod_path:
        raise BadRequest(f'Invalid pod path: {pod_path!r}')
    normalized = posixpath.normpath('/' + pod_path.lstrip('/'))
    parts = [p for p in pod_path.split('/') if p]
    if any(p in ('.', '..') for p in parts):
        raise BadRequest(f'Path traversal is not permitted: {pod_path!r}')
    return normalized


def _sanitize_filename(filename):
    if not filename or '\x00' in filename:
        raise BadRequest('Invalid filename')
    base = os.path.basename(filename.replace('\\', '/'))
    if not base or base in ('.', '..'):
        raise BadRequest(f'Invalid filename: {filename!r}')
    return base


class PodApi:
    """Basic pod API."""

    EDITOR_FILE_NAME = '_editor.yaml'
    TEMPLATE_FILE_NAME = '_template.yaml'
    STRINGS_PATH = '/content/strings'
    IGNORED_BRANCHES = ('HEAD',)
    IGNORED_PREFIXES = ('.', '_')
    IGNORED_EXTS = ('.pyc',)
    IGNORED_DIRS = (
        '/backend/',
        '/build/',
        '/ext/',
        '/extensions/',
        '/node_modules/',
    )
    MIME_TO_TYPE = {
        'image/jpeg': 'jpg',
        'image/png': 'png',
        'image/svg+xml': 'svg',
        'image/webp': 'webp',
        'image/gif': 'gif',
    }

    def __init__(self, pod, request, matched):
        self.pod = pod
        self.request = request
        self.matched = matched
        self.data = {}
        try:
            self.ext_config = self.pod.extensions_controller.extension_config(
                'extensions.editor.EditorExtension'
            )
        except AttributeError:
            self.ext_config = {}
        self.handle_request()

    @property
    def response(self):
        data = json.dumps(self.data, cls=json_encoder.GrowJSONEncoder)
        return wrappers.Response(data, mimetype='application/json')

    def _editor_config(self, doc):
        fields = doc.format.front_matter.data
        config = fields.get('$editor')
        if config:
            return config
        collection = doc.collection
        editor_path = os.path.join(collection.pod_path, self.EDITOR_FILE_NAME)
        if not self.pod.file_exists(editor_path):
            return {}
        return self.pod.read_yaml(editor_path) or {}

    def _editor_config_partial(self, partial):
        editor_path = f'{partial.pod_path}/{self.EDITOR_FILE_NAME}'
        if self.pod.file_exists(editor_path):
            return self.pod.read_yaml(editor_path) or {}
        return {}

    def _format_screenshot_base(self, path, key):
        if not path.endswith('/'):
            path = f'{path}/'
        return f'{path}{key}'.strip('/')

    def _get_param(self, param_name):
        try:
            return self.request.params.get(param_name)
        except AttributeError:
            return self.request.args.get(param_name)

    def _get_post(self, param_name, is_file=False):
        try:
            return self.request.POST.get(param_name)
        except AttributeError:
            if is_file:
                return self.request.files[param_name]
            return self.request.form.get(param_name)

    def _get_resolutions(self):
        screenshot_config = self.ext_config.get('screenshots', {})
        resolutions_raw = screenshot_config.get(
            'resolutions',
            [
                {
                    'width': 1280,
                    'height': 1600,
                }
            ],
        )
        return [screenshot.ScreenshotResolution(r['width'], r['height']) for r in resolutions_raw]

    def _get_screenshot_dir(self):
        screenshot_config = self.ext_config.get('screenshots', {})
        return screenshot_config.get('static_dir', screenshot.DEFAULT_SCREENSHOT_DIR)

    def _get_collection_templates(self, collection):
        template_pod_path = os.path.join(collection.pod_path, self.TEMPLATE_FILE_NAME)
        if self.pod.file_exists(template_pod_path):
            return self.pod.read_yaml(template_pod_path)
        return {}

    def _has_post(self, param_name):
        try:
            return param_name in self.request.POST
        except AttributeError:
            return param_name in self.request.form

    def _is_ignored_dir(self, full_path):
        ignored_dirs = tuple(self.ext_config.get('ignored_dirs', ()))
        return full_path.startswith(self.IGNORED_DIRS + ignored_dirs)

    def _is_ignored_name(self, file_name):
        ignored_prefixes = tuple(self.ext_config.get('ignored_prefixes', ()))
        ignored_exts = tuple(self.ext_config.get('ignored_exts', ()))
        return file_name.startswith(self.IGNORED_PREFIXES + ignored_prefixes) or file_name.endswith(
            self.IGNORED_EXTS + ignored_exts
        )

    def _load_doc(self, pod_path):
        pod_path = _validate_pod_path(pod_path)
        doc = self.pod.get_doc(pod_path)

        if not doc.exists:
            return {
                'pod_path': doc.pod_path,
                'editor': self._editor_config(doc),
                'front_matter': {},
                'serving_paths': {},
                'default_locale': str(doc.default_locale),
                'locales': [str(locale) for locale in doc.locales],
                'raw_front_matter': '',
                'content': '',
                'hash': None,
            }

        serving_paths = {}
        try:
            serving_path = doc.get_serving_path()
            serving_paths[str(doc.default_locale)] = serving_path
            for key, value in doc.get_serving_paths_localized().items():
                serving_paths[str(key)] = value
        except document.PathFormatError:
            pass

        raw_front_matter = doc.format.front_matter.export()
        if raw_front_matter:
            front_matter = yaml.load(raw_front_matter, Loader=yaml_utils.PlainTextYamlLoader)
        else:
            front_matter = {}

        return {
            'pod_path': doc.pod_path,
            'editor': self._editor_config(doc),
            'front_matter': front_matter,
            'serving_paths': serving_paths,
            'default_locale': str(doc.default_locale),
            'locales': [str(locale) for locale in doc.locales],
            'raw_front_matter': raw_front_matter,
            'content': doc.body,
            'hash': self.pod.hash_file(pod_path),
        }

    def _load_static_doc(self, pod_path):
        pod_path = _validate_pod_path(pod_path)
        static_doc = self.pod.get_static(pod_path)
        return {
            'pod_path': static_doc.pod_path,
            'serving_url': static_doc.url.path,
        }

    @staticmethod
    def force_string(value):
        try:
            return value.decode('utf-8')
        except (UnicodeDecodeError, AttributeError):
            return value

    def content_from_template(self):
        collection_path = _validate_pod_path(self._get_param('collection_path'))
        key = self._get_param('key')
        file_name = _sanitize_filename((self._get_param('file_name') or '').strip())
        collection = self.pod.get_collection(collection_path)
        templates = self._get_collection_templates(collection)

        template_meta = templates.get(key) or templates.get('_default')

        if not template_meta:
            pod_path = _validate_pod_path(posixpath.join(collection.pod_path, file_name))
            self.pod.write_file(pod_path, '')
            return

        file_ext = template_meta.get('extension')
        if file_ext and not file_name.endswith(file_ext):
            file_name = f'{file_name}.{file_ext}'

        pod_path = _validate_pod_path(posixpath.join(collection.pod_path, file_name))
        doc = document.Document(pod_path, _pod=self.pod, _collection=collection)
        doc.format.update(
            fields=template_meta.get('front_matter'), content=template_meta.get('content')
        )
        doc.write()

    def copy_pod_path(self):
        pod_path = _validate_pod_path(self._get_param('pod_path'))
        new_pod_path = _validate_pod_path(self._get_param('new_pod_path'))
        if not self.pod.file_exists(pod_path):
            raise BadRequest(f'{pod_path} does not exist in the pod')
        if self.pod.file_exists(new_pod_path):
            raise BadRequest(f'{new_pod_path} would overwrite an existing file in the pod')
        self.pod.write_file(new_pod_path, self.pod.read_file(pod_path))

    def delete_pod_path(self):
        pod_path = _validate_pod_path(self._get_param('pod_path'))
        if not self.pod.file_exists(pod_path):
            raise BadRequest(f'{pod_path} does not exist in the pod')
        self.pod.delete_file(pod_path)

    def get_pod_paths(self):
        pod_paths = []
        for root, dirs, files in self.pod.walk('/'):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            pod_dir = root.replace(self.pod.root, '')
            for file_name in files:
                if self._is_ignored_name(file_name):
                    continue
                full_path = os.path.join(pod_dir, file_name)
                if self._is_ignored_dir(full_path):
                    continue
                pod_paths.append(full_path)

        self.data = {'pod_paths': pod_paths}

    def get_editor_content(self):
        pod_path = self._get_param('pod_path')
        self.data = self._load_doc(pod_path)

    def get_extension_config(self):
        extension_path = self._get_param('extension_path')
        try:
            ext_config = self.pod.extensions_controller.extension_config(extension_path)
        except AttributeError:
            ext_config = {}
        self.data = ext_config

    def get_partials(self):
        partials = {}
        screenshot_pod_dir = self._get_screenshot_dir()

        for partial in self.pod.partials.get_partials():
            partials[partial.key] = partial.config.get('editor', {})
            screenshots = {}
            examples = partials[partial.key].get('examples', [])
            for example in examples:
                screenshots[example] = {}
                screenshot_file_base = self._format_screenshot_base(partial.key, example)
                for resolution in self._get_resolutions():
                    screenshot_pod_path = os.path.join(
                        screenshot_pod_dir, 'partials', resolution.filename(screenshot_file_base)
                    )
                    if self.pod.file_exists(screenshot_pod_path):
                        screenshots[example][resolution.resolution] = self._load_static_doc(
                            screenshot_pod_path
                        )
            partials[partial.key]['screenshots'] = screenshots

        self.data = {'partials': partials}

    def get_pod(self):
        self.data = {'pod': {'title': self.pod.podspec.title}}

    def get_routes(self):
        routes = {}
        router = grow_router.Router(self.pod)
        router.use_simple()
        router.add_all(concrete=True)
        for path, node_info, _options in router.routes.nodes:
            if node_info.kind in ('doc', 'static'):
                routes[path] = {
                    'pod_path': node_info.meta['pod_path'],
                    'locale': node_info.meta.get('locale'),
                }
        self.data = {'routes': routes}

    def get_static_serving_path(self):
        pod_path = _validate_pod_path(self._get_param('pod_path'))
        static_doc = self.pod.get_static(pod_path)
        self.data = {
            'pod_path': pod_path,
            'serving_url': static_doc.url.path,
        }

    def get_strings(self):
        strings = {}
        pod_paths = []
        for root, _dirs, files in self.pod.walk(self.STRINGS_PATH):
            pod_dir = root.replace(self.pod.root, '')
            for file_name in files:
                if not file_name.startswith(self.IGNORED_PREFIXES):
                    pod_paths.append(os.path.join(pod_dir, file_name))

        for pod_path in pod_paths:
            strings[pod_path] = self.pod.read_yaml(pod_path)

        self.data = {'strings': strings}

    def get_repo(self):
        remote_name = self._get_param('remote') or 'origin'
        repo = utils.get_git_repo(self.pod.root)
        if not repo:
            return {}
        branch = str(repo.active_branch)
        revision = repo.git.rev_list('--count', 'HEAD')
        remote_url = None
        web_url = None
        remote = None
        for repo_remote in repo.remotes:
            if repo_remote.name == remote_name:
                remote = repo_remote
                break

        if remote:
            urls = list(remote.urls)
            remote_url = urls and urls[0]
            web_url = remote_url
            if web_url:
                web_url = web_url.replace('git@github.com:', 'https://www.github.com/')
                if web_url.endswith('.git'):
                    web_url = web_url[:-4]
                web_url = web_url.replace(
                    'https://source.developers.google.com/p/', 'https://source.cloud.google.com/'
                )
                web_url = web_url.replace('/r/', '/')

        if not remote:
            remote = repo.remote()

        branch_names = ['/'.join(ref.name.split('/')[1:]) for ref in remote.refs]
        branches = [name for name in branch_names if name not in self.IGNORED_BRANCHES]

        commits = []
        if repo.head.ref:
            for commit in repo.iter_commits(branch, max_count=10):
                committed_date = datetime.datetime.fromtimestamp(
                    commit.committed_date, tz=datetime.timezone.utc
                )
                commits.append(
                    {
                        'message': commit.message,
                        'commit_date': committed_date.isoformat(),
                        'sha': commit.hexsha,
                        'author': {
                            'name': commit.author.name,
                            'email': commit.author.email,
                        },
                    }
                )

        self.data = {
            'repo': {
                'web_url': web_url,
                'remote_url': remote_url,
                'revision': revision,
                'branch': branch,
                'branches': branches,
                'commits': commits,
            },
        }
        return self.data

    def get_templates(self):
        templates = {}
        collections = self.pod.list_collections()
        screenshot_pod_dir = self._get_screenshot_dir()

        for collection in collections:
            template_info = self._get_collection_templates(collection)
            if not template_info:
                continue

            templates[collection.pod_path] = {}
            for key, template_meta in template_info.items():
                screenshots = {}
                screenshot_file_base = self._format_screenshot_base(collection.pod_path, key)
                for resolution in self._get_resolutions():
                    screenshot_pod_path = os.path.join(
                        screenshot_pod_dir, resolution.filename(screenshot_file_base)
                    )
                    if self.pod.file_exists(screenshot_pod_path):
                        screenshots[resolution.resolution] = self._load_static_doc(
                            screenshot_pod_path
                        )

                templates[collection.pod_path][key] = {
                    'label': template_meta.get('label', key),
                    'description': template_meta.get('description', ''),
                    'screenshots': screenshots,
                }

        self.data = {'templates': templates}

    def handle_request(self):
        path = self.matched.params['path']
        method = self.request.method
        if path == 'content':
            if method == 'GET':
                self.get_editor_content()
            elif method == 'POST':
                self.post_editor_content()
        elif path == 'content/copy':
            if method == 'GET':
                self.copy_pod_path()
        elif path == 'content/delete':
            if method == 'GET':
                self.delete_pod_path()
        elif path == 'content/template':
            if method == 'GET':
                self.content_from_template()
        elif path == 'extension/config':
            if method == 'GET':
                self.get_extension_config()
        elif path == 'image':
            if method == 'POST':
                self.post_image()
        elif path == 'partials':
            if method == 'GET':
                self.get_partials()
        elif path == 'strings':
            if method == 'GET':
                self.get_strings()
        elif path == 'routes':
            if method == 'GET':
                self.get_routes()
        elif path == 'pod_paths':
            if method == 'GET':
                self.get_pod_paths()
        elif path == 'pod':
            if method == 'GET':
                self.get_pod()
        elif path == 'repo':
            if method == 'GET':
                self.get_repo()
        elif path == 'static_serving_path':
            if method == 'GET':
                self.get_static_serving_path()
        elif path == 'templates':
            if method == 'GET':
                self.get_templates()
        else:
            raise NotFound(f'{path} not found.')

    def post_editor_content(self):
        pod_path = _validate_pod_path(self._get_post('pod_path'))
        doc = self.pod.get_doc(pod_path)
        if self._has_post('raw_front_matter'):
            front_matter_content = self.force_string(self._get_post('raw_front_matter'))
            doc.format.front_matter.update_raw_front_matter(front_matter_content)
            if self._has_post('content'):
                content = self.force_string(self._get_post('content'))
                doc.write(body=content)
            else:
                doc.write()
        elif self._has_post('front_matter'):
            fields = json.loads(self._get_post('front_matter'))
            fields = yaml_conversion.convert_fields(fields)
            if self._has_post('content'):
                content = self.force_string(self._get_post('content'))
                doc.write(fields=fields, body=content)
            else:
                doc.write(fields=fields)

        self.pod.podcache.document_cache.remove(doc)
        self.data = self._load_doc(pod_path)

    def post_image(self):
        destination = _validate_pod_path(self._get_post('destination'))
        upload_file = self._get_post('file', is_file=True)
        try:
            file_contents = upload_file.file.read()
        except AttributeError:
            file_contents = upload_file.read()

        filename = upload_file.filename
        if filename == 'blob' or not filename:
            mime_type = getattr(upload_file, 'type', None) or getattr(upload_file, 'mimetype', None)
            if mime_type not in self.MIME_TO_TYPE:
                raise BadRequest(f'Unsupported image MIME type: {mime_type!r}')
            file_extension = self.MIME_TO_TYPE[mime_type]
            digest = hashlib.sha256(file_contents).hexdigest()
            filename = f'{digest}.{file_extension}'
        else:
            filename = _sanitize_filename(filename)

        pod_path = _validate_pod_path(posixpath.join(destination, filename))
        self.pod.write_file(pod_path, file_contents)
        self.data = self._load_static_doc(pod_path)


def serve_api(pod, request, matched, **_kwargs):
    api = PodApi(pod, request, matched)
    return api.response
