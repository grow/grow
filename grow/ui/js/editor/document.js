/**
 * Document for the editor.
 */

import DeepObject from '../utility/deepObject'
import { fieldGenerator } from './field'

export default class Document {
  constructor(podPath, fieldMeta, frontMatter, servingPaths, defaultLocale) {
    this.podPath = podPath
    this.fieldMeta = fieldMeta
    this.frontMatter = new DeepObject(frontMatter)
    this.servingPaths = servingPaths
    this.defaultLocale = defaultLocale
    this.fields = []

    for (const meta of this.fieldMeta) {
      const field = fieldGenerator(meta['type'], meta['key'])
      field.value = this.frontMatter.get(meta['key'])
      field.label = meta['label']
      this.fields.push(field)
    }
  }

  get servingPath() {
    return this.servingPaths[this.defaultLocale]
  }
}
