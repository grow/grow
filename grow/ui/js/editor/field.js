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

export class ListField extends Field {
  constructor(key, config, list) {
    super(key, 'list', config)
    this.list = list
    this.fieldsEl = this.fieldEl.querySelector('.list__list')
    this.fields = []
  }

  get labelEl() {
    if (!this._labelEl) {
      this._labelEl = this.fieldEl.querySelector('.list__label')
    }
    return this._labelEl
  }

  get value() {
    const values = []
    for (const field of this.fields) {
      values.push(field.value)
    }
    return values
  }

  set value(frontMatter) {
    for (const item of frontMatter) {
      const field = fieldGenerator(
        this.config.get('sub_type', 'text'), `${this.key}[]`,
        this.config.get('sub_config', {}), this.list)
      field.value = item
      this.fields.push(field)
      this.fieldsEl.appendChild(field.fieldEl)
    }
  }

  update(value) {
    // TODO: Figure out how to pass the updated list data into the container.
    // for (const container of this.fields) {
    //   container.update()
    // }
  }
}

export class PartialsField extends ListField {
  constructor(key, config, list) {
    super(key, config, list)
  }

  set value(frontMatter) {
    this.list.deferredPartials.promise.then((listMeta) => {
      for (const item of frontMatter) {
        const partialMeta = listMeta[item['partial']]
        const field = new PartialContainer(
          item['partial'], partialMeta['label'], item, partialMeta['fields'])
        this.fields.push(field)
        this.fieldsEl.appendChild(field.fieldEl)
      }
    })
  }

  update(value) {
    // TODO: Figure out how to pass the updated list data into the container.
    // for (const field of this.fields) {
    //   field.update()
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

export function fieldGenerator(type, key, config, list) {
  switch (type) {
    case 'list':
      return new ListField(key, config, list)
      break
    case 'partials':
      return new PartialsField(key, config, list)
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
