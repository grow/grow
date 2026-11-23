"""Grow preprocessor for importing Greenhouse job boards (stdlib-only)."""

import html
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

from protorpc import messages

import grow

REQUEST_TIMEOUT_SECONDS = 30
_BOARD_TOKEN_RE = re.compile(r'^[A-Za-z0-9_-]+$')
_JOB_ID_RE = re.compile(r'^[0-9]+$')
_URL_ATTRS = frozenset({'href', 'src', 'action', 'formaction'})
_SAFE_URL_SCHEMES = frozenset({'http', 'https', 'mailto', ''})
_VOID_TAGS = frozenset({'br', 'hr', 'img', 'input', 'meta', 'link', 'area', 'col', 'wbr'})
_SKIP_CONTENT_TAGS = frozenset({'script', 'style'})


class Error(Exception):
    pass


class _AllowlistHTMLSanitizer(HTMLParser):
    """Stdlib HTML sanitizer that strips disallowed tags and unsafe URLs."""

    def __init__(self, allowed_tags, allowed_attributes=None):
        super().__init__(convert_charrefs=True)
        self.allowed_tags = frozenset(t.lower() for t in allowed_tags)
        self.allowed_attributes = {
            k.lower(): frozenset(a.lower() for a in v)
            for k, v in (allowed_attributes or {}).items()
        }
        self._skip_depth = 0
        self._out = []

    def _is_safe_attr(self, tag, name, value):
        lower_name = name.lower()
        if lower_name.startswith('on'):
            return False
        allowed_for_tag = self.allowed_attributes.get(
            tag, frozenset()
        ) | self.allowed_attributes.get('*', frozenset())
        if lower_name not in allowed_for_tag:
            return False
        if lower_name in _URL_ATTRS and value is not None:
            scheme = urllib.parse.urlsplit(value.strip()).scheme.lower()
            if scheme not in _SAFE_URL_SCHEMES:
                return False
        return True

    def handle_starttag(self, tag, attrs):
        lower = tag.lower()
        if lower in _SKIP_CONTENT_TAGS and lower not in self.allowed_tags:
            self._skip_depth += 1
            return
        if self._skip_depth > 0 or lower not in self.allowed_tags:
            return
        safe_attrs = []
        for name, value in attrs:
            if not self._is_safe_attr(lower, name, value):
                continue
            if value is None:
                safe_attrs.append(name.lower())
            else:
                safe_attrs.append(f'{name.lower()}="{html.escape(value, quote=True)}"')
        attr_str = (' ' + ' '.join(safe_attrs)) if safe_attrs else ''
        self._out.append(f'<{lower}{attr_str}>')

    def handle_endtag(self, tag):
        lower = tag.lower()
        if lower in _SKIP_CONTENT_TAGS and lower not in self.allowed_tags:
            if self._skip_depth > 0:
                self._skip_depth -= 1
            return
        if self._skip_depth > 0 or lower not in self.allowed_tags or lower in _VOID_TAGS:
            return
        self._out.append(f'</{lower}>')

    def handle_data(self, data):
        if self._skip_depth > 0:
            return
        self._out.append(html.escape(data, quote=False))

    def get_html(self):
        return ''.join(self._out)


def sanitize_html(content, allowed_tags, allowed_attributes=None):
    """Sanitizes HTML keeping only allowlisted tags and safe attributes."""
    parser = _AllowlistHTMLSanitizer(allowed_tags, allowed_attributes)
    parser.feed(content)
    parser.close()
    return parser.get_html()


def _fetch_json(url, timeout=REQUEST_TIMEOUT_SECONDS):
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'grow-ext-greenhouse/2.0'},
        method='GET',
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                raise Error(f'Error requesting -> {url}')
            return json.loads(resp.read().decode('utf-8'))
    except (urllib.error.URLError, ValueError, OSError):
        raise Error(f'Error requesting -> {url}')


class AttributeMessage(messages.Message):
    tag = messages.StringField(1)
    attributes = messages.StringField(2, repeated=True)


class GreenhousePreprocessor(grow.Preprocessor):
    KIND = 'greenhouse'
    DEGREES_URL = 'https://api.greenhouse.io/v1/boards/{board_token}/education/degrees'
    DEPARTMENTS_URL = 'https://api.greenhouse.io/v1/boards/{board_token}/departments'
    DISCIPLINES_URL = 'https://api.greenhouse.io/v1/boards/{board_token}/education/disciplines'
    JOBS_URL = 'https://api.greenhouse.io/v1/boards/{board_token}/jobs?content=true'
    JOB_URL = 'https://api.greenhouse.io/v1/boards/{board_token}/jobs/{job_id}?questions=true'
    SCHOOLS_URL = 'https://api.greenhouse.io/v1/boards/{board_token}/education/schools'

    class Config(messages.Message):
        board_token = messages.StringField(1)
        jobs_collection = messages.StringField(2)
        departments_collection = messages.StringField(3)
        allowed_html_tags = messages.StringField(4, repeated=True)
        allowed_html_attributes = messages.MessageField(AttributeMessage, 5, repeated=True)
        education_path = messages.StringField(6)
        departments_blacklist = messages.StringField(7, repeated=True)
        job_title_filter = messages.StringField(8)

    @staticmethod
    def _validate_board_token(board_token):
        if not board_token or not _BOARD_TOKEN_RE.match(board_token):
            raise Error(f'Invalid Greenhouse board_token: {board_token!r}')
        return board_token

    @staticmethod
    def _validate_job_id(job_id):
        job_id_str = str(job_id)
        if not _JOB_ID_RE.match(job_id_str):
            raise Error(f'Invalid Greenhouse job_id: {job_id!r}')
        return job_id_str

    def bind_jobs(self, board_token, collection_path):
        token = self._validate_board_token(board_token)
        url = GreenhousePreprocessor.JOBS_URL.format(board_token=token)
        content = _fetch_json(url)
        self._bind(collection_path, content['jobs'])

    def _download_schools(self, board_token):
        token = self._validate_board_token(board_token)
        schools = {'items': []}
        total = 0
        items_so_far = 0
        page = 1
        has_run = False
        while not has_run or items_so_far < total:
            self.pod.logger.info(f'Downloading schools (page {page})')
            url = f'{GreenhousePreprocessor.SCHOOLS_URL.format(board_token=token)}?page={page}'
            resp = _fetch_json(url)
            if not has_run:
                has_run = True
                total = resp.get('meta', {}).get('total_count', 0)
            batch = resp.get('items', [])
            if not batch:
                break
            schools['items'] += batch
            items_so_far += len(batch)
            page += 1
        return schools

    def bind_education(self, board_token, education_path):
        token = self._validate_board_token(board_token)
        schools = self._download_schools(token)
        degrees = _fetch_json(GreenhousePreprocessor.DEGREES_URL.format(board_token=token))
        disciplines = _fetch_json(GreenhousePreprocessor.DISCIPLINES_URL.format(board_token=token))
        item = {
            'degrees': degrees,
            'disciplines': disciplines,
            'schools': schools,
        }
        path = os.path.join(education_path)
        self.pod.write_yaml(path, item)
        self.pod.logger.info(f'Saving -> {path}')

    def _parse_entry(self, item):
        if item.get('title'):
            item['$title'] = item.pop('title')
        if item.get('content'):
            item['content'] = self._parse_content(item.get('content'))
        if item.get('compliance'):
            for i, row in enumerate(item['compliance']):
                if row.get('description'):
                    item['compliance'][i]['description'] = self._parse_content(row['description'])
        return item

    def _parse_content(self, content):
        content = html.unescape(content)
        tags = self.config.allowed_html_tags
        if tags:
            attributes = {}
            if self.config.allowed_html_attributes:
                for attribute in self.config.allowed_html_attributes:
                    attributes[attribute.tag] = list(attribute.attributes)
            content = sanitize_html(content, tags, attributes)
        return content

    def _get_single_job(self, item):
        token = self._validate_board_token(self.config.board_token)
        job_id = self._validate_job_id(item['id'])
        url = GreenhousePreprocessor.JOB_URL.format(board_token=token, job_id=job_id)
        return _fetch_json(url)

    def _bind(self, collection_path, items):
        existing_paths = self.pod.list_dir(collection_path)
        existing_basenames = [path.lstrip('/') for path in existing_paths]
        departments_blacklist = [name.lower() for name in (self.config.departments_blacklist or [])]
        new_basenames = []
        for item in items:
            department_names = [
                department.get('name', '').lower() for department in item.get('departments', [])
            ]
            skip = False
            for name in department_names:
                if name in departments_blacklist:
                    self.pod.logger.info(f'Skipping department -> {name}')
                    skip = True
            if skip:
                continue
            item = self._get_single_job(item)
            item = self._parse_entry(item)
            if self.config.job_title_filter and self.config.job_title_filter not in item.get(
                '$title', ''
            ):
                continue
            job_id = self._validate_job_id(item['id'])
            path = os.path.join(collection_path, f'{job_id}.yaml')
            self.pod.write_yaml(path, item)
            self.pod.logger.info(f'Saving -> {path}')
            new_basenames.append(os.path.basename(path))
        basenames_to_delete = set(existing_basenames) - set(new_basenames)
        for basename in basenames_to_delete:
            if basename.startswith('_'):
                continue
            path = os.path.join(collection_path, basename)
            self.pod.delete_file(path)
            self.pod.logger.info(f'Deleting -> {path}')

    def run(self, *args, **kwargs):
        if self.config.jobs_collection:
            self.bind_jobs(self.config.board_token, self.config.jobs_collection)
        if self.config.education_path:
            self.bind_education(self.config.board_token, self.config.education_path)
