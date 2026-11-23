"""Grow preprocessor for importing Google Forms into YAML (stdlib-only)."""

import html as html_lib
import json
import re
import urllib.error
import urllib.request
from html.parser import HTMLParser

from protorpc import messages, protojson

from grow.preprocessors import google_drive

REQUEST_TIMEOUT_SECONDS = 30
_FORM_ID_RE = re.compile(r'^[A-Za-z0-9_-]+$')
_VOID_TAGS = frozenset({'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta'})

TRANSLATABLE_KEYS = (
    'description',
    'label',
    'placeholder',
    'title',
    'value',
)

SIGN_IN_PAGE_SENTINEL = '<title>Google Forms - create and analyze surveys, for free.</title>'


def nl2br(value):
    paragraph_re = re.compile(r'(?:\r\n|\r(?!\n)|\n){2,}')
    return '\n\n'.join(
        f'<p>{p.replace(chr(10), "<br>" + chr(10))}</p>' for p in paragraph_re.split(value)
    )


class Error(Exception):
    pass


class _Element:
    """Minimal stdlib DOM node supporting BeautifulSoup-like queries."""

    def __init__(self, tag, attrs=None, parent=None):
        self.tag = tag
        self.attrs = dict(attrs or {})
        self.parent = parent
        self.children = []

    @property
    def contents(self):
        return self.children

    def get(self, key, default=None):
        return self.attrs.get(key, default)

    def __getitem__(self, key):
        return self.attrs[key]

    @property
    def text(self):
        parts = []
        for child in self.children:
            if isinstance(child, str):
                parts.append(child)
            else:
                parts.append(child.text)
        return ''.join(parts)

    def _render(self):
        if self.tag == '#document':
            return self.decode_contents()
        attr_parts = []
        for k, v in self.attrs.items():
            if v is None:
                attr_parts.append(k)
            else:
                attr_parts.append(f'{k}="{html_lib.escape(str(v), quote=True)}"')
        attr_str = (' ' + ' '.join(attr_parts)) if attr_parts else ''
        if self.tag in _VOID_TAGS:
            return f'<{self.tag}{attr_str}>'
        return f'<{self.tag}{attr_str}>{self.decode_contents()}</{self.tag}>'

    def __str__(self):
        return self._render()

    def decode_contents(self):
        parts = []
        for child in self.children:
            if isinstance(child, str):
                parts.append(html_lib.escape(child, quote=False))
            else:
                parts.append(child._render())
        return ''.join(parts)

    def _matches(self, name, attrs):
        if name is not None and self.tag != name:
            return False
        if attrs:
            for k, expected in attrs.items():
                actual = self.attrs.get(k)
                if actual is None:
                    return False
                if k == 'class':
                    classes = actual.split()
                    if isinstance(expected, (list, tuple, set)):
                        if not any(c in classes for c in expected):
                            return False
                    elif expected not in classes:
                        return False
                elif actual != expected:
                    return False
        return True

    def find_all(self, name=None, attrs=None):
        results = []
        for child in self.children:
            if isinstance(child, _Element):
                if child._matches(name, attrs):
                    results.append(child)
                results.extend(child.find_all(name, attrs))
        return results

    findAll = find_all

    def find(self, name=None, attrs=None):
        for child in self.children:
            if isinstance(child, _Element):
                if child._matches(name, attrs):
                    return child
                found = child.find(name, attrs)
                if found is not None:
                    return found
        return None


class _DOMParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = _Element('#document')
        self._stack = [self.root]

    def handle_starttag(self, tag, attrs):
        lower = tag.lower()
        el = _Element(lower, attrs, parent=self._stack[-1])
        self._stack[-1].children.append(el)
        if lower not in _VOID_TAGS:
            self._stack.append(el)

    def handle_startendtag(self, tag, attrs):
        el = _Element(tag.lower(), attrs, parent=self._stack[-1])
        self._stack[-1].children.append(el)

    def handle_endtag(self, tag):
        lower = tag.lower()
        for idx in range(len(self._stack) - 1, 0, -1):
            if self._stack[idx].tag == lower:
                del self._stack[idx:]
                break

    def handle_data(self, data):
        self._stack[-1].children.append(data)


def _parse_html(markup):
    parser = _DOMParser()
    parser.feed(markup)
    parser.close()
    return parser.root


def _ancestor(node, levels):
    curr = node
    for _ in range(levels):
        if curr is None:
            return None
        curr = curr.parent
    return curr


def _remap_translatable_keys(data):
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            remapped = _remap_translatable_keys(value)
            if isinstance(key, str) and value and key in TRANSLATABLE_KEYS:
                result[f'{key}@'] = remapped
            else:
                result[key] = remapped
        return result
    if isinstance(data, list):
        return [_remap_translatable_keys(item) for item in data]
    return data


class FieldType(messages.Enum):
    TEXT = 1
    TEXTAREA = 2
    CHECKBOX = 3
    RADIO = 4
    SCALE = 5
    DATE = 6


class Field(messages.Message):
    placeholder = messages.StringField(3)
    field_type = messages.EnumField(FieldType, 4)
    name = messages.StringField(5)
    value = messages.StringField(6)


class Header(messages.Message):
    title = messages.StringField(1)
    body = messages.StringField(2)


class GridRow(messages.Message):
    fields = messages.MessageField(Field, 1, repeated=True)
    label = messages.StringField(2)


class Item(messages.Message):
    label = messages.StringField(1)
    description = messages.StringField(2)
    fields = messages.MessageField(Field, 3, repeated=True)
    grid = messages.MessageField(GridRow, 6, repeated=True)
    required = messages.BooleanField(4)
    header = messages.MessageField(Header, 5)


class Form(messages.Message):
    title = messages.StringField(1)
    description = messages.StringField(2)
    items = messages.MessageField(Item, 3, repeated=True)
    action = messages.StringField(4)


class GoogleFormsPreprocessor(google_drive.BaseGooglePreprocessor):
    KIND = 'google_forms'
    VIEW_URL = 'https://docs.google.com/forms/d/e/{}/viewform?hl=en'
    ACTION_URL = 'https://docs.google.com/forms/d/e/{}/formResponse?hl=en'

    class Config(messages.Message):
        id = messages.StringField(1)
        path = messages.StringField(2)
        translate = messages.BooleanField(3, default=True)

    @staticmethod
    def _validate_form_id(form_id):
        if not form_id or not _FORM_ID_RE.match(form_id):
            raise Error(f'Invalid Google Form ID: {form_id!r}')
        return form_id

    def run(self, *args, **kwargs):
        form_id = self._validate_form_id(self.config.id)
        url = GoogleFormsPreprocessor.VIEW_URL.format(form_id)
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'grow-ext-google-forms/2.0'},
            method='GET',
        )
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
                if resp.status != 200:
                    raise Error(f'Error requesting -> {url}')
                markup = resp.read().decode('utf-8', errors='replace')
        except (urllib.error.URLError, OSError):
            raise Error(f'Error requesting -> {url}')

        if SIGN_IN_PAGE_SENTINEL in markup:
            raise Error(f'Error requesting -> {url} -> Are you sure the form is publicly viewable?')
        soup = _parse_html(markup)
        soup_content = soup.find('div', {'class': 'freebirdFormviewerViewFormContent'})
        if soup_content is None:
            raise Error(f'Unable to locate form content in -> {url}')
        form_msg = self.parse_form(soup_content)
        msg_string_content = protojson.encode_message(form_msg)
        json_dict = json.loads(msg_string_content)
        if self.config.translate:
            json_dict = self.tag_keys_for_translation(json_dict)
        self.pod.write_yaml(self.config.path, json_dict)
        self.pod.logger.info(f'Saved -> {self.config.path}')

    def tag_keys_for_translation(self, data):
        return _remap_translatable_keys(data)

    def get_html(self, soup, class_name):
        el = soup.find('div', {'class': class_name})
        if not el:
            return None
        return ''.join(str(part) for part in el.contents)

    def get_text(self, soup, class_name):
        el = soup.find('div', {'class': class_name})
        return el.text if el else None

    def get_placeholder(self, soup, class_name='quantumWizTextinputPaperinputPlaceholder'):
        el = soup.find('div', {'class': class_name})
        return el.text if el else None

    def get_description(self, soup):
        el = soup.find('div', {'class': 'freebirdFormviewerViewItemsItemItemHelpText'})
        return el.text if el else None

    def get_choice_value(self, soup):
        el = soup.find('div', {'class': 'docssharedWizToggleLabeledPrimaryText'})
        return el.text if el else None

    def get_header(self, soup):
        header = Header()
        title = soup.find('div', {'class': 'freebirdFormviewerViewItemsSectionheaderTitle'})
        if title:
            header.title = title.text
        body = soup.find(
            'div', {'class': 'freebirdFormviewerViewItemsSectionheaderDescriptionText'}
        )
        if body:
            header.body = body.decode_contents()
        if header.title or header.body:
            return header
        return None

    def parse_form(self, soup):
        form_id = self._validate_form_id(self.config.id)
        msg = Form()
        msg.title = self.get_text(soup, 'freebirdFormviewerViewHeaderTitle')
        msg.description = self.get_html(soup, 'freebirdFormviewerViewHeaderDescription')
        msg.action = GoogleFormsPreprocessor.ACTION_URL.format(form_id)
        msg.items = []
        items = soup.find_all('div', {'class': 'freebirdFormviewerViewNumberedItemContainer'})
        for item in items:
            item_msg = Item()
            item_msg.required = bool(
                item.find(
                    'span', {'class': 'freebirdFormviewerComponentsQuestionBaseRequiredAsterisk'}
                )
            )
            item_msg.label = self.get_text(item, 'exportItemTitle')
            if item_msg.required and item_msg.label and item_msg.label.endswith(' *'):
                item_msg.label = item_msg.label[:-2]
            item_msg.description = self.get_description(item)
            item_msg.header = self.get_header(item)
            item_msg.fields = []

            params = [div['data-params'] for div in item.find_all() if 'data-params' in div.attrs]
            input_names = []
            if params:
                entry_ids = re.findall(r'\[([0-9]+)', params[0])[1:]
                input_names = [f'entry.{entry_id}' for entry_id in entry_ids if len(entry_id) > 1]

            grid_rows = item.find_all(
                'div', {'class': 'freebirdFormviewerComponentsQuestionGridRowGroup'}
            )
            if grid_rows:
                header = item.find(
                    'div', {'class': 'freebirdFormviewerComponentsQuestionGridColumnHeader'}
                )
                input_values = (
                    [
                        field.text
                        for field in header.find_all(
                            'div', {'class': 'freebirdFormviewerComponentsQuestionGridCell'}
                        )
                    ]
                    if header
                    else []
                )
                item_msg.grid = []
                for row in grid_rows:
                    label = row.find(
                        'div', {'class': 'freebirdFormviewerComponentsQuestionGridRowHeader'}
                    )
                    local_hidden_inputs = row.find_all('input', {'type': 'hidden'})
                    choices = row.find_all(
                        'div', {'class': 'freebirdFormviewerComponentsQuestionGridCell'}
                    )
                    grid_row = GridRow()
                    grid_row.fields = []
                    grid_row.label = label.text if label else ''
                    for n, _choice in enumerate(choices):
                        if not local_hidden_inputs or n >= len(input_values):
                            continue
                        field_msg = Field()
                        field_msg.field_type = FieldType.RADIO
                        field_msg.name = local_hidden_inputs[0].get('name')
                        field_msg.value = input_values[n]
                        if field_msg.value:
                            grid_row.fields.append(field_msg)
                    if grid_row.label:
                        item_msg.grid.append(grid_row)

            checkboxes = item.find_all(
                'div', {'class': 'freebirdFormviewerComponentsQuestionCheckboxChoice'}
            )
            for checkbox in checkboxes:
                parent = _ancestor(checkbox, 2)
                inputs = parent.find_all('input') if parent else []
                field_msg = Field()
                field_msg.field_type = FieldType.CHECKBOX
                field_msg.name = inputs[-1].get('name') if inputs else None
                field_msg.value = self.get_choice_value(checkbox)
                item_msg.fields.append(field_msg)

            scales = item.find_all('div', {'class': 'freebirdMaterialScalecontentLabel'})
            for scale in scales:
                parent = _ancestor(scale, 6)
                inp = parent.find('input') if parent else None
                field_msg = Field()
                field_msg.field_type = FieldType.SCALE
                field_msg.name = inp.get('name') if inp else None
                field_msg.value = scale.text
                item_msg.fields.append(field_msg)

            radios = item.find_all(
                'div', {'class': 'freebirdFormviewerComponentsQuestionRadioChoice'}
            )
            for radio in radios:
                parent = _ancestor(radio, 6)
                inputs = parent.find_all('input') if parent else []
                field_msg = Field()
                field_msg.field_type = FieldType.RADIO
                field_msg.name = inputs[-1].get('name') if inputs else None
                field_msg.value = self.get_choice_value(radio)
                item_msg.fields.append(field_msg)

            textareas = item.find_all('div', {'class': 'freebirdFormviewerViewItemsTextLongText'})
            for text in textareas:
                field_msg = Field()
                field_msg.field_type = FieldType.TEXTAREA
                field_msg.placeholder = self.get_placeholder(
                    text, class_name='quantumWizTextinputPapertextareaPlaceholder'
                )
                field_msg.name = input_names[0] if input_names else None
                item_msg.fields.append(field_msg)

            texts = item.find_all('div', {'class': 'freebirdFormviewerComponentsQuestionTextRoot'})
            for text in texts:
                field_msg = Field()
                field_msg.field_type = FieldType.TEXT
                field_msg.placeholder = self.get_placeholder(text)
                field_msg.name = input_names[0] if input_names else None
                item_msg.fields.append(field_msg)

            dates = item.find_all(
                'div', {'class': 'freebirdFormviewerComponentsQuestionDateInputsContainer'}
            )
            for date in dates:
                field_msg = Field()
                field_msg.field_type = FieldType.DATE
                field_msg.placeholder = self.get_placeholder(date)
                field_msg.name = input_names[0] if input_names else None
                item_msg.fields.append(field_msg)

            msg.items.append(item_msg)
        return msg
