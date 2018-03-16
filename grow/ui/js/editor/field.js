/**
 * Fields for the editor.
 */

import Config from '../utility/config'
import { PartialContainer } from './partial'

export default class Field {
  constructor(key, type, config) {
    // Create the field clone before setting any attributes.
    this.template = document.querySelector(`#template_field_${type}`)
    this.fieldEl = document.importNode(this.template.content, true)

    this.key = key
    this.type = type
    this.isFocused = false
    this.config = new Config(config || {})
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

  monitorFocus() {
    this.inputEl.addEventListener('blur', () => { this.isFocused = false })
    this.inputEl.addEventListener('focus', () => { this.isFocused = true })
  }

  update(value) {
    // Respect the user focus to not overwrite on auto save.
    if (this.isFocused) {
      return
    }
    this.value = value
  }
}

export class TextField extends Field {
  constructor(key, config) {
    super(key, 'text', config)
    this.monitorFocus()
  }

  set key(value) {
    super.key = value
    this.inputEl.setAttribute('id', value)
    this.labelEl.setAttribute('for', value)
  }
}

export class PartialsField extends Field {
  constructor(key, config, partials) {
    super(key, 'partials', config)
    this.partials = partials
    this.fieldsEl = this.fieldEl.querySelector('.partials__partials')
    this.containers = []
  }

  get labelEl() {
    if (!this._labelEl) {
      this._labelEl = this.fieldEl.querySelector('.partials__label')
    }
    return this._labelEl
  }

  get value() {
    const values = []
    for (const container of this.containers) {
      values.push(container.value)
    }
    return values
  }

  set value(frontMatter) {
    this.partials.deferredPartials.promise.then((partialsMeta) => {
      for (const item of frontMatter) {
        const partialMeta = partialsMeta[item['partial']]
        const container = new PartialContainer(
          item['partial'], partialMeta['label'], item, partialMeta['fields'])
        this.containers.push(container)
        this.fieldsEl.appendChild(container.fieldEl)
      }
    })
  }

  update(value) {
    // TODO: Figure out how to pass the updated partials data into the container.
    // for (const container of this.containers) {
    //   container.update()
    // }
  }
}

export class TextAreaField extends Field {
  constructor(key, config) {
    super(key, 'textarea', config)
    this.monitorFocus()
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

export function fieldGenerator(type, key, config, partials) {
  switch (type) {
    case 'partials':
      return new PartialsField(key, config, partials)
      break
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
