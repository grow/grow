/**
 * Content editor.
 */

 import Config from '../utility/config'
import Document from './document'
import EditorApi from './editorApi'
import Partials from './partial'
import { MDCIconToggle } from '@material/icon-toggle'
import { MDCLinearProgress } from '@material/linear-progress'
import { MDCTextField } from '@material/textfield'


export default class Editor {
  constructor(containerEl, config) {
    this.containerEl = containerEl
    this.config = new Config(config || {})
    this.mobileToggleEl = this.containerEl.querySelector('#content_device')
    this.contentPreviewEl = this.containerEl.querySelector('.content__preview')
    this.autosaveEl = this.containerEl.querySelector('#autosave')
    this.previewEl = this.containerEl.querySelector('.preview')
    this.fieldsEl = this.containerEl.querySelector('.fields')
    this.saveEl = this.containerEl.querySelector('.sidebar__save button')
    this.podPathEl = this.containerEl.querySelector('#pod_path')
    this.host = this.previewEl.dataset.host
    this.port = this.previewEl.dataset.port
    this.fields = []
    this.document = null
    this.autosaveID = null

    this.autosaveEl.addEventListener('click', this.handleAutosaveClick.bind(this))
    this.saveEl.addEventListener('click', this.handleSaveClick.bind(this))

    this.mobileToggleMd = MDCIconToggle.attachTo(this.mobileToggleEl)
    this.mobileToggleEl.addEventListener(
      'MDCIconToggle:change', this.handleMobileClick.bind(this))
    this.podPathMd = new MDCTextField(
      this.containerEl.querySelector('.content__path .mdc-text-field'))
    this.saveProgressMd = MDCLinearProgress.attachTo(
      this.containerEl.querySelector('.sidebar__save .mdc-linear-progress'))
    this.saveProgressMd.close()

    this.api = new EditorApi({
      host: this.host,
      port: this.port,
    })
    this.partials = new Partials(this.api)
    this.loadDetails(this.podPath)

    // TODO Start the autosave depending on local storage.
    // this.startAutosave()
  }

  get autosave() {
    return this.autosaveEl.checked
  }

  get podPath() {
    return this.podPathEl.value
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
    // Update the reference to be the attached element.
    field.fieldEl = this.fieldsEl.children[this.fieldsEl.children.length - 1]
    field.setup()
  }

  clearFields() {
    this.fields = []
    while (this.fieldsEl.firstChild) {
      this.fieldsEl.removeChild(this.fieldsEl.firstChild)
    }
  }

  handleAutosaveClick(evt) {
    if (this.autosaveEl.checked) {
      this.startAutosave()
    } else {
      this.stopAutosave()
    }
  }

  handleMobileClick(evt) {
    if (evt.detail.isOn) {
      this.containerEl.classList.add('container--mobile')
      this.previewEl.classList.add('mdc-elevation--z4')
    } else {
      this.containerEl.classList.remove('container--mobile')
      this.previewEl.classList.remove('mdc-elevation--z4')
    }
  }

  handleGetDocumentResponse(response) {
    // Update the url if the document loaded is a different pod path.
    const basePath = this.config.get('base', '/_grow/editor')
    const origPath = window.location.pathname
    const newPath = `${basePath}${response['pod_path']}`
    const isChangedPodPath = origPath != newPath
    if (isChangedPodPath) {
      history.pushState({}, '', newPath)
    }

    this.document = new Document(
      response['pod_path'],
      response['fields'],
      response['front_matter'],
      response['serving_paths'],
      response['default_locale'],
      this.partials)

    this.clearFields()

    for (const field of this.document.fields) {
      this.addField(field)
    }

    this.previewEl.src = this.previewUrl
  }

  handleSaveDocumentResponse(response) {
    this.saveProgressMd.close()
    this.document.update(
      response['pod_path'],
      response['front_matter'],
      response['serving_paths'],
      response['default_locale'])

    this.previewEl.src = this.previewUrl
  }

  handleSaveClick() {
    this.save()
  }

  loadDetails(podPath) {
    this.api.getDocument(podPath).then(this.handleGetDocumentResponse.bind(this))
  }

  save() {
    this.saveProgressMd.open()
    const frontMatter = {}
    for (const field of this.fields) {
      // Field key getter not working...?!?
      frontMatter[field._key] = field.value
    }
    const result = this.api.saveDocument(this.podPath, frontMatter, this.document.locale)
    result.then(this.handleSaveDocumentResponse.bind(this))
  }

  startAutosave() {
    if (this.autosaveID) {
      this.stopAutosave()
    }

    this.autosaveID = window.setInterval(() => {
      this.save()
    }, this.config.get('autosaveInterval', 1000))

    this.autosaveEl.checked = true
  }

  stopAutosave() {
    if (this.autosaveID) {
      window.clearInterval(this.autosaveID)
    }

    this.autosaveEl.checked = false
  }
}
