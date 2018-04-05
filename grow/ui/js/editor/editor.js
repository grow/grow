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
import expandObject from '../utility/expandObject'


export default class Editor {
  constructor(containerEl, config) {
    this.containerEl = containerEl
    this.config = new Config(config || {})
    this.mobileToggleEl = this.containerEl.querySelector('#content_device')
    this.sourceToggleEl = this.containerEl.querySelector('#content_source')
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
    this._isEditingSource = false

    this.autosaveEl.addEventListener('click', this.handleAutosaveClick.bind(this))
    this.saveEl.addEventListener('click', () => { this.save(true) })

    this.mobileToggleMd = MDCIconToggle.attachTo(this.mobileToggleEl)
    this.mobileToggleEl.addEventListener(
      'MDCIconToggle:change', this.handleMobileClick.bind(this))
    this.sourceToggleMd = MDCIconToggle.attachTo(this.sourceToggleEl)
    this.sourceToggleEl.addEventListener(
      'MDCIconToggle:change', this.handleSourceClick.bind(this))
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

    // Default to loading with the UI.
    this.loadSource(this.podPath)

    // TODO Start the autosave depending on local storage.
    // this.startAutosave()
  }

  get autosave() {
    return this.autosaveEl.checked
  }

  get isClean() {
    for (const field of this.fields) {
      if (!field.isClean) {
        return false
      }
    }
    return true
  }

  get isEditingSource() {
    return this._isEditingSource
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

  documentFromResponse(response) {
    this.document = new Document(
      response['pod_path'],
      response['editor']['fields'],
      response['front_matter'],
      response['raw_front_matter'],
      response['serving_paths'],
      response['default_locale'],
      this.partials)

    this.clearFields()
  }

  handleAutosaveClick(evt) {
    if (this.autosaveEl.checked) {
      this.startAutosave()
    } else {
      this.stopAutosave()
    }
  }

  handleLoadFieldsResponse(response) {
    this._isEditingSource = false
    this.documentFromResponse(response)
    this.pushState(this.document.podPath)
    this.showFields()
    this.refreshPreview()
  }

  handleLoadSourceResponse(response) {
    this._isEditingSource = true
    this.documentFromResponse(response)
    this.pushState(this.document.podPath)
    this.showSource()
    this.refreshPreview()
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

  handleSaveFieldsResponse(response) {
    this.saveProgressMd.close()
    this.document.update(
      response['pod_path'],
      response['front_matter'],
      response['raw_front_matter'],
      response['serving_paths'],
      response['default_locale'])

    this.refreshPreview()
  }

  handleSaveSourceResponse(response) {
    this.saveProgressMd.close()
    this.document.update(
      response['pod_path'],
      response['front_matter'],
      response['raw_front_matter'],
      response['serving_paths'],
      response['default_locale'])

    this.refreshPreview()
  }

  handleSourceClick(evt) {
    if (evt.detail.isOn) {
      this.loadSource(this.podPath)
    } else {
      this.loadFields(this.podPath)
    }
  }

  loadFields(podPath) {
    this.api.getDocument(podPath).then(this.handleLoadFieldsResponse.bind(this))
  }

  loadSource(podPath) {
    this.api.getDocument(podPath).then(this.handleLoadSourceResponse.bind(this))
  }

  pushState(podPath) {
    // Update the url if the document loaded is a different pod path.
    const basePath = this.config.get('base', '/_grow/editor')
    const origPath = window.location.pathname
    const newPath = `${basePath}${podPath}`
    if (origPath != newPath) {
      history.pushState({}, '', newPath)
    }
  }

  refreshPreview() {
    if (this.previewEl.src == this.previewUrl) {
      this.previewEl.contentWindow.location.reload(true)
    } else {
      this.previewEl.src = this.previewUrl
    }
  }

  save(force) {
    this.saveProgressMd.open()
    if (this.isClean && !force) {
      this.saveProgressMd.close()
    } else if (this.isEditingSource) {
      const rawFrontMatter = this.fields[0].value // Source field
      const result = this.api.saveDocumentSource(this.podPath, rawFrontMatter)
      result.then(this.handleSaveSourceResponse.bind(this))
    } else {
      const shortFrontMatter = {}
      for (const field of this.fields) {
        // Field key getter not working...?!?
        shortFrontMatter[field._key] = field.value
      }
      const frontMatter = expandObject(shortFrontMatter)
      const result = this.api.saveDocumentFields(this.podPath, frontMatter, this.document.locale)
      result.then(this.handleSaveFieldsResponse.bind(this))
    }
  }

  showFields() {
    this.clearFields()
    this.containerEl.classList.remove('container--source')
    for (const field of this.document.fields) {
      this.addField(field)
    }
  }

  showSource() {
    this.clearFields()
    this.containerEl.classList.add('container--source')
    for (const field of this.document.sourceFields) {
      this.addField(field)
    }
  }

  startAutosave() {
    if (this.autosaveID) {
      this.stopAutosave()
    }

    this.autosaveID = window.setInterval(() => {
      this.save()
    }, this.config.get('autosaveInterval', 2000))

    this.autosaveEl.checked = true
  }

  stopAutosave() {
    if (this.autosaveID) {
      window.clearInterval(this.autosaveID)
    }

    this.autosaveEl.checked = false
  }
}
