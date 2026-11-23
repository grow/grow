"""Tests for google_forms extension."""

import pytest

from google_forms import Error, FieldType, GoogleFormsPreprocessor, google_forms_preprocessor


def _make_preprocessor(form_id='1FAIpQLScExample_123'):
    class _FakePod:
        root = '/tmp'
        logger = None

    config = GoogleFormsPreprocessor.Config(id=form_id, path='/content/form.yaml', translate=True)
    return GoogleFormsPreprocessor(_FakePod(), config)


def test_rejects_invalid_form_id():
    pre = _make_preprocessor(form_id='../../evil?foo=1')
    with pytest.raises(Error, match='Invalid Google Form ID'):
        pre.run()


def test_tag_keys_for_translation_stdlib():
    pre = _make_preprocessor()
    data = {
        'title': 'Contact',
        'action': 'https://docs.google.com/forms/d/e/abc/formResponse',
        'items': [{'label': 'Name', 'required': True, 'description': ''}],
    }
    tagged = pre.tag_keys_for_translation(data)
    assert tagged['title@'] == 'Contact'
    assert tagged['action'] == data['action']
    assert tagged['items'][0]['label@'] == 'Name'
    assert 'description' in tagged['items'][0]  # empty value not suffixed


def test_parse_form_extracts_title_and_text_input():
    pre = _make_preprocessor()
    markup = """
    <div class="freebirdFormviewerViewFormContent">
      <div class="freebirdFormviewerViewHeaderTitle">Survey</div>
      <div class="freebirdFormviewerViewNumberedItemContainer">
        <div data-params="%.@.[123,[456789]]"></div>
        <div class="exportItemTitle">Your name *</div>
        <span class="freebirdFormviewerComponentsQuestionBaseRequiredAsterisk">*</span>
        <div class="freebirdFormviewerComponentsQuestionTextRoot">
          <div class="quantumWizTextinputPaperinputPlaceholder">Jane Doe</div>
        </div>
      </div>
    </div>
    """
    soup = google_forms_preprocessor._parse_html(markup)
    content = soup.find('div', {'class': 'freebirdFormviewerViewFormContent'})
    form = pre.parse_form(content)
    assert form.title == 'Survey'
    assert len(form.items) == 1
    assert form.items[0].required is True
    assert form.items[0].label == 'Your name'
    assert form.items[0].fields[0].field_type == FieldType.TEXT
    assert form.items[0].fields[0].name == 'entry.456789'
    assert form.items[0].fields[0].placeholder == 'Jane Doe'
