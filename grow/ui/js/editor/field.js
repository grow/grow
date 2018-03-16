/**
 * Fields for the editor.
 */

import Config from '../utility/config'

export default class Field {
  constructor(key, type, config) {
    // Create the field clone before setting any attributes.
    this.template = document.querySelector(`#template_field_${type}`)
    this.fieldEl = document.importNode(this.template.content, true)

    this.key = key
    this.type = type
    this.config = new Config(config || {})
    this.dirty = false
    this.original
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

  get label() {
    return this.labelEl.innerText
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

  set label(value) {
    this._label = value
    this.labelEl.innerText = value
  }

  set value(value) {
    this.inputEl.value = value
  }

  update(value) {
    // TODO: Make this respect the user's current editing to not overwrite on auto save.
    this.value = value
  }
}

export class TextField extends Field {
  constructor(key, config) {
    super(key, 'text', config)
  }

  set key(value) {
    super.key = value
    this.inputEl.setAttribute('id', value)
    this.labelEl.setAttribute('for', value)
  }
}

export class TextAreaField extends Field {
  constructor(key, config) {
    super(key, 'textarea', config)
  }

  get inputEl() {
    if (!this._inputEl) {
      this._inputEl = this.fieldEl.querySelector('textarea')
    }
    return this._inputEl
  }

  set key(value) {
    super.key = value
    this.inputEl.setAttribute('id', value)
    this.labelEl.setAttribute('for', value)
  }
}

export function fieldGenerator(type, key, config) {
  switch (type) {
    case 'text':
      return new TextField(key, config)
      break
    case 'textarea':
      return new TextAreaField(key, config)
      break
    default:
      throw('Unknown field type')
  }
}