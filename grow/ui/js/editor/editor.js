/**
 * Content editor.
 */

import { TextField } from './field'

export default class Editor {
  constructor(containerEl) {
    this.containerEl = containerEl
    this.mobileToggleEl = this.containerEl.querySelector('#content_device')
    this.contentPreviewEl = this.containerEl.querySelector('.content__preview')
    this.previewEl = this.containerEl.querySelector('.preview')
    this.fieldsEl = this.containerEl.querySelector('.fields')

    this.mobileToggleEl.addEventListener('click', this.handleMobileClick.bind(this))

    this.clearFields()

    const field = new TextField('$path')
    this.addField(field)
  }

  addField(field) {
    this.fieldsEl.appendChild(field.fieldEl)
  }

  clearFields() {
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
}
