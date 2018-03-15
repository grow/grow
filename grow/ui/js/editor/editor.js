/**
 * Content editor.
 */

import Document from './document'

// Stub for what a future request will look like.
const fauxResponseDetails = {
  'pod_path': '/content/pages/home.yaml',
  'fields': [
    {
      'type': 'text',
      'key': '$path',
      'label': 'Serving Path',
    },
    {
      'type': 'textarea',
      'key': 'description',
      'label': 'Description',
    },
  ],
  'front_matter': {
    '$path': '/',
    'description': 'Something really cool.',
  },
  'serving_paths': {
    'en': '/',
  },
  'default_locale': 'en',
}


export default class Editor {
  constructor(containerEl) {
    this.containerEl = containerEl
    this.mobileToggleEl = this.containerEl.querySelector('#content_device')
    this.contentPreviewEl = this.containerEl.querySelector('.content__preview')
    this.previewEl = this.containerEl.querySelector('.preview')
    this.fieldsEl = this.containerEl.querySelector('.fields')
    this.host = this.previewEl.dataset.host
    this.port = this.previewEl.dataset.port
    this.fields = []
    this.document = null

    this.mobileToggleEl.addEventListener('click', this.handleMobileClick.bind(this))

    this.loadDetails('/content/pages/home.yaml')
  }

  get previewUrl() {
    return `http://${this.host}:${this.port}${this.servingPath}`
  }

  get servingPath() {
    if (!this.document) {
      return ''
    }
    return this.document.servingPath
  }

  addField(field) {
    this.fields.push(field)
    this.fieldsEl.appendChild(field.fieldEl)
  }

  clearFields() {
    this.fields = []
    while (this.fieldsEl.firstChild) {
      this.fieldsEl.removeChild(this.fieldsEl.firstChild)
    }
  }

  handleMobileClick() {
    if (this.mobileToggleEl.checked) {
      this.contentPreviewEl.classList.add('content__preview--mobile')
      this.previewEl.classList.add('mdl-shadow--6dp')
    } else {
      this.contentPreviewEl.classList.remove('content__preview--mobile')
      this.previewEl.classList.remove('mdl-shadow--6dp')
    }
  }

  handleDetailResponse(response) {
    this.document = new Document(
      response['pod_path'],
      response['fields'],
      response['front_matter'],
      response['serving_paths'],
      response['default_locale'])

    this.clearFields()

    for (const field of this.document.fields) {
      this.addField(field)
    }

    this.previewEl.src = this.previewUrl
  }

  loadDetails(podPath) {
    // TODO: This should be done by making a request to the server.
    this.handleDetailResponse(fauxResponseDetails)
  }
}
