/**
 * Document for the editor.
 */

import DeepObject from '../utility/deepObject'
import { fieldGenerator } from './field'

export default class Document {
  constructor(podPath, fieldMeta, frontMatter, rawFrontMatter, servingPaths, defaultLocale, partials) {
    this.podPath = podPath
    this.fieldMeta = fieldMeta
    this.frontMatter = new DeepObject(frontMatter)
    this.rawFrontMatter = rawFrontMatter
    this.servingPaths = servingPaths
    this.defaultLocale = defaultLocale
    this.locale = defaultLocale
    this.partials = partials
    this.fields = []
    this.sourceFields = []

    // Fields.
    for (const meta of this.fieldMeta) {
      const field = fieldGenerator(meta['type'], meta['key'], meta, this.partials)
      field.value = this.frontMatter.get(meta['key'])
      field.label = meta['label']
      this.fields.push(field)
    }

    // Source Fields.
    const field = fieldGenerator('source')
    field.value = this.rawFrontMatter
    this.sourceFields.push(field)
  }

  get servingPath() {
    return this.servingPaths[this.defaultLocale]
  }

  update(podPath, frontMatter, rawFrontMatter, servingPaths, defaultLocale) {
    this.podPath = podPath
    this.frontMatter = new DeepObject(frontMatter)
    this.rawFrontMatter = rawFrontMatter
    this.servingPaths = servingPaths
    this.defaultLocale = defaultLocale
    this.locale = defaultLocale

    // Check which values in the fields have changed and update.
    for (const field of this.fields) {
      // Field key getter not working...?!?
      field.update(this.frontMatter.get(field._key))
    }

    // Currently only a source field...
    for (const field of this.sourceFields) {
      // Field key getter not working...?!?
      field.update(this.rawFrontMatter)
    }
  }
}
