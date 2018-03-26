/**
 * Fields for the editor.
 */

import Config from '../utility/config'
import pell from 'pell'
import marked from 'marked'
import TurndownService from 'turndown'
import { PartialContainer } from './partial'
import { MDCTextField } from '@material/textfield'


const availableFields = {}

export default class Field {
  constructor(key, type, config) {
    // Create the field clone before setting any attributes.
    this.template = document.querySelector(`#template_field_${type}`)
    this.fieldEl = document.importNode(this.template.content, true)

    this.key = key
    this.type = type
    this.isFocused = false
    this.config = new Config(config || {})
    this._cleanValue = null
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

  get isClean() {
    return this._cleanValue == this.value
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
    this._cleanValue = value
  }

  monitorFocus() {
    this.inputEl.addEventListener('blur', () => { this.isFocused = false })
    this.inputEl.addEventListener('focus', () => { this.isFocused = true })
  }

  setup() {
    // Do nothing.
  }

  update(value) {
    // Respect the user focus to not overwrite on auto save.
    if (this.isFocused) {
      // Need to save the updated clean value for comparison.
      this._cleanValue = value
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

  get mdEl() {
    if (!this._mdEl) {
      this._mdEl = this.fieldEl.querySelector('.mdc-text-field')
    }
    return this._mdEl
  }

  set key(value) {
    super.key = value
    this.inputEl.setAttribute('id', value)
    this.labelEl.setAttribute('for', value)
  }

  setup() {
    this.fieldMd = new MDCTextField(this.mdEl)
  }
}

export class ListField extends Field {
  constructor(key, config, list) {
    super(key, 'list', config)
    this.list = list
    this.fieldsEl = this.fieldEl.querySelector('.list__list')
    this.fields = []
  }

  get isClean() {
    for (const field of this.fields) {
      if (!field.isClean) {
        return false
      }
    }
    return true
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
      // Update the reference to be the attached element.
      field.fieldEl = this.fieldsEl.children[this.fieldsEl.children.length - 1]
      field.setup()
    }
  }

  update(value) {
    for (const idx in this.fields) {
      // TODO This could break if the list change order or type externally
      // and when the partial length doesn't match.
      this.fields[idx].update(value[idx])
    }
  }
}

export class MarkdownField extends Field {
  constructor(key, config) {
    super(key, 'markdown', config)
    this.monitorFocus()
  }

  get editor() {
    if (!this._editor) {
      this._editor = pell.init({
        element: this.inputEl,
        actions: ['bold', 'italic', 'heading1', 'heading2', 'olist', 'ulist', 'link'],
        onChange: () => {}
      })
    }
    return this._editor
  }

  get inputEl() {
    if (!this._inputEl) {
      this._inputEl = this.fieldEl.querySelector('.pell')
    }
    return this._inputEl
  }

  get labelEl() {
    if (!this._labelEl) {
      this._labelEl = this.fieldEl.querySelector('.field__markdown__label')
    }
    return this._labelEl
  }

  get turndownService() {
    if (!this._turndown) {
      this._turndown = new TurndownService({ headingStyle: 'atx' })
    }
    return this._turndown
  }

  get value() {
    return this.turndownService.turndown(this.editor.content.innerHTML)
  }

  set value(value) {
    this.editor.content.innerHTML = marked(value)
    this._cleanValue = value
  }

  monitorFocus() {
    this.editor.content.addEventListener('blur', () => { this.isFocused = false })
    this.editor.content.addEventListener('focus', () => { this.isFocused = true })
  }
}

export class PartialsField extends ListField {
  constructor(key, config, list) {
    super(key, config, list)
  }

  get value() {
    return super.value
  }

  set value(frontMatter) {
    this.list.deferredPartials.promise.then((listMeta) => {
      for (const item of frontMatter) {
        const partialMeta = listMeta[item['partial']]
        const field = new PartialContainer(
          item['partial'], partialMeta['label'], item, partialMeta['fields'])
        field.listeners.add('remove', this.handleRemovePartial.bind(this))
        this.fields.push(field)
        this.fieldsEl.appendChild(field.fieldEl)
        // Update the reference to be the attached element.
        field.fieldEl = this.fieldsEl.children[this.fieldsEl.children.length - 1]
      }
    })
  }

  handleRemovePartial(partial) {
    partial.remove()
    this.fields = this.fields.filter(item => item !== partial)
  }

  update(value) {
    for (const idx in this.fields) {
      // TODO This will break if the partials change order externally
      // and when the partial length doesn't match.
      this.fields[idx].update(value[idx])
    }
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

  get mdEl() {
    if (!this._mdEl) {
      this._mdEl = this.fieldEl.querySelector('.mdc-text-field')
    }
    return this._mdEl
  }

  set key(value) {
    super.key = value
    this.inputEl.setAttribute('id', value)
    this.labelEl.setAttribute('for', value)
  }

  setup() {
    this.fieldMd = new MDCTextField(this.mdEl)
  }
}

availableFields['list'] = ListField
availableFields['partials'] = PartialsField
availableFields['text'] = TextField
availableFields['textarea'] = TextAreaField
availableFields['markdown'] = MarkdownField

export function fieldGenerator(type, key, config, list) {
  if (!type in availableFields) {
    throw('Unknown field type')
  }
  return new availableFields[type](key, config, list)
}
