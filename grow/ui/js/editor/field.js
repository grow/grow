/**
 * Fields for the editor.
 */

export default class Field {
  constructor(key, type) {
    // Create the field clone before setting any attributes.
    this.template = document.querySelector(`#template_field_${type}`)
    this.fieldEl = document.importNode(this.template.content, true)

    this.key = key
    this.type = type
  }

  get inputEl() {
    if (!this._inputEl) {
      this._inputEl = this.fieldEl.querySelector('input')
    }
    return this._inputEl
  }

  get key() {
    return this._key
  }

  get labelEl() {
    if (!this._labelEl) {
      this._labelEl = this.fieldEl.querySelector('label')
    }
    return this._labelEl
  }

  get value() {
    return this.inputEl.value
  }

  set key(value) {
    this._key = value
  }

  set value(value) {
    this.inputEl.setAttribute('value', value)
  }
}

export class TextField extends Field {
  constructor(key) {
    super(key, 'text')
  }

  set key(value) {
    this._key = value
    this.inputEl.setAttribute('id', value)
    this.labelEl.setAttribute('for', value)
  }
}
