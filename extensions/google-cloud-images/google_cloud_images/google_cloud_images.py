"""Grow extension for Google Cloud Images dynamic image serving."""

import json
import os
import urllib.error
import urllib.parse
import urllib.request

import jinja2
from jinja2.ext import Extension
from protorpc import messages

import grow

REQUEST_TIMEOUT_SECONDS = 30


class Error(Exception):
    pass


__preprocessor = None


def _get_preprocessor(pod):
    global __preprocessor
    if __preprocessor is not None and __preprocessor.pod is pod:
        return __preprocessor
    for preprocessor in pod.list_preprocessors():
        if preprocessor.KIND == GoogleCloudImagesPreprocessor.KIND:
            __preprocessor = preprocessor
            return preprocessor
    return None


def get_placeholder(bucket_path, placeholders):
    _, ext = os.path.splitext(bucket_path)
    if ext not in placeholders:
        raise Error(f'No placeholder found for GCS path -> {bucket_path}')
    return placeholders.get(ext)


def _build_request_url(backend, params):
    parsed = urllib.parse.urlsplit(backend)
    existing = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    merged = existing + list(params.items())
    return urllib.parse.urlunsplit(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            urllib.parse.urlencode(merged),
            parsed.fragment,
        )
    )


def get_image_serving_data(
    backend,
    bucket_path,
    locale=None,
    fuzzy_extensions=None,
    logger=None,
    placeholders=None,
    is_placeholder=False,
    api_key=None,
    timeout=REQUEST_TIMEOUT_SECONDS,
):
    """Requests serving URL and metadata from the Google Cloud Images backend."""
    params = {'gs_path': bucket_path}
    if locale:
        params['locale'] = str(locale)

    url = _build_request_url(backend, params)
    headers = {'User-Agent': 'grow-ext-google-cloud-images/2.0'}
    token = api_key or os.environ.get('GROW_GCI_API_KEY', '').strip()
    if token:
        headers['Authorization'] = f'Bearer {token}'

    req = urllib.request.Request(url, headers=headers, method='GET')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                raise ValueError(f'Unexpected status: {resp.status}')
            data = json.loads(resp.read().decode('utf-8'))
            return data, not is_placeholder
    except (urllib.error.URLError, ValueError, OSError):
        if fuzzy_extensions:
            base, original_ext = os.path.splitext(bucket_path)
            if original_ext not in ('.jpg', '.png'):
                raise Error('Fuzzy extensions only supports .png and .jpg files.')
            new_ext = '.jpg' if original_ext == '.png' else '.png'
            alt_bucket_path = base + new_ext
            if logger:
                logger.info(f'Trying fuzzy extension -> {alt_bucket_path}')
            return get_image_serving_data(
                backend,
                alt_bucket_path,
                locale=locale,
                fuzzy_extensions=False,
                logger=logger,
                placeholders=placeholders,
                api_key=api_key,
                timeout=timeout,
            )
        if placeholders:
            if logger:
                logger.warning(
                    f'Error with Google Cloud Images URL (using placeholder instead) -> {bucket_path}'
                )
            placeholder_path = get_placeholder(bucket_path, placeholders)
            return get_image_serving_data(
                backend,
                placeholder_path,
                locale=locale,
                fuzzy_extensions=False,
                logger=logger,
                is_placeholder=True,
                api_key=api_key,
                timeout=timeout,
            )
        raise Error(f'An error occurred generating a Google Cloud Images URL for: {bucket_path}')


class GoogleImage:
    def __init__(self, pod, bucket_path, locale=None, original_locale=None, fuzzy_extensions=False):
        self.pod = pod
        self.locale = locale
        self.original_locale = original_locale
        self.bucket_path = bucket_path
        self._base_url = None
        self._backend = None
        self._placeholders = None
        self._fuzzy_extensions = fuzzy_extensions
        self._cache = None
        self.__data = None

    def __repr__(self):
        return f'<GoogleImage {self.bucket_path}>'

    @property
    def cache(self):
        if self._cache is None:
            podcache = self.pod.podcache
            ident = 'ext-google-cloud-images'
            self._cache = podcache.get_object_cache(ident, write_to_file=True)
        return self._cache

    @property
    def placeholders(self):
        if self._placeholders is None:
            preprocessor = _get_preprocessor(self.pod)
            self._placeholders = preprocessor.extensions_to_placeholders()
        return self._placeholders

    @property
    def backend(self):
        if self._backend is None:
            preprocessor = _get_preprocessor(self.pod)
            self._backend = preprocessor.config.backend
        return self._backend

    @property
    def _data(self):
        if self.__data is None:
            image_serving_data = self.cache.get(self._cache_key)
            if image_serving_data is not None:
                self.__data = image_serving_data
            else:
                if self.locale and '{locale}' in self.bucket_path:
                    if self.locale != self.original_locale:
                        message = (
                            f'Generating Google Cloud Images data -> '
                            f'{self.bucket_path} ({self.locale} for {self.original_locale})'
                        )
                    else:
                        message = (
                            f'Generating Google Cloud Images data -> '
                            f'{self.bucket_path} ({self.locale})'
                        )
                else:
                    message = f'Generating Google Cloud Images data -> {self.bucket_path}'
                self.pod.logger.info(message)
                data, use_cache = get_image_serving_data(
                    self.backend,
                    self.bucket_path,
                    locale=self.locale,
                    fuzzy_extensions=self._fuzzy_extensions,
                    logger=self.pod.logger,
                    placeholders=self.placeholders,
                )
                if use_cache:
                    self.cache.add(self._cache_key, data)
                self.__data = data
        return self.__data

    @property
    def _cache_key(self):
        if '{locale}' in self.bucket_path:
            return f'{self.backend}:{self.bucket_path}:{self.locale}:metadata'
        return f'{self.backend}:{self.bucket_path}:metadata'

    @property
    def base_url(self):
        """Returns a URL corresponding to the image served by Google's
        image-serving infrastructure."""
        if self._base_url is None:
            self._base_url = self._data['url']
        return self._base_url

    @property
    def content_type(self):
        return self._data['content_type']

    @property
    def created(self):
        return self._data['created']

    @property
    def dimensions(self):
        return f'{self.width}x{self.height}'

    @property
    def etag(self):
        return self._data['etag']

    @property
    def height(self):
        return self._data['image_metadata'].get('height')

    @property
    def size(self):
        return self._data['size']

    def url(self, options=None):
        if not options:
            return self.base_url
        return f'{self.base_url}={"-".join(options)}'

    @property
    def width(self):
        return self._data['image_metadata'].get('width')


class GoogleCloudImagesExtension(Extension):
    def __init__(self, environment):
        super().__init__(environment)
        environment.globals['google_image'] = GoogleCloudImagesExtension.create_google_image

    @staticmethod
    @jinja2.pass_context
    def create_google_image(ctx, bucket_path, fuzzy_extensions=False):
        if 'doc' not in ctx:
            raise Error(
                'Missing `doc` in the template context. Are'
                ' you using `google_image` within a macro? Remember to {%'
                ' import ... with context %}.'
            )
        doc = ctx['doc']
        pod = doc.pod
        locale = doc.locale
        # Supports aliasing one locale to another, for example we can say all
        # `es_PR` pages should use `en_US` assets.
        # Either pull the locale from a global rewrite from podspec, or pull
        # from a key `google_cloud_images_locale` on the document.
        if 'google_cloud_images_locale' in doc.fields and doc.google_cloud_images_locale:
            locale = doc.google_cloud_images_locale
        else:
            preprocessor = _get_preprocessor(doc.pod)
            if preprocessor and preprocessor.config.rewrite_locales:
                for rewrite_locales in preprocessor.config.rewrite_locales:
                    if locale == rewrite_locales.rewrite:
                        locale = rewrite_locales.to
        return GoogleImage(
            pod,
            bucket_path,
            locale=locale,
            original_locale=doc.locale,
            fuzzy_extensions=fuzzy_extensions,
        )


class RewriteLocalesMessage(messages.Message):
    rewrite = messages.StringField(1)
    to = messages.StringField(2)


class PlaceholderMessage(messages.Message):
    extensions = messages.StringField(1, repeated=True)
    path = messages.StringField(2)


class GoogleCloudImagesPreprocessor(grow.Preprocessor):
    KIND = 'google_cloud_images'
    _extensions_to_placeholders = None

    class Config(messages.Message):
        backend = messages.StringField(1)
        rewrite_locales = messages.MessageField(RewriteLocalesMessage, 2, repeated=True)
        placeholders = messages.MessageField(PlaceholderMessage, 3, repeated=True)

    def run(self, *args, **kwargs):
        self.pod.logger.info(f'Using Google Cloud images backend -> {self.config.backend}')

    def extensions_to_placeholders(self):
        if self._extensions_to_placeholders is None:
            self._extensions_to_placeholders = {}
            if self.config.placeholders:
                for placeholder in self.config.placeholders:
                    for ext in placeholder.extensions:
                        self._extensions_to_placeholders[ext] = placeholder.path
        return self._extensions_to_placeholders
