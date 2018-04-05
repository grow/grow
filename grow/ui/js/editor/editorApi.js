/**
 * Utility for working with apis.
 */

import Api from '../utility/api'
import Defer from '../utility/defer'

export default class EditorApi extends Api {
  constructor(config) {
    super(config)
  }

  getDocument(podPath) {
    const result = new Defer()

    this.request.get(this.apiPath('editor/content'))
      .query({ 'pod_path': podPath })
      .then((res) => {
        result.resolve(res.body)
      })

    return result.promise
  }

  getPartials(podPath) {
    const result = new Defer()

    this.request.get(this.apiPath('editor/partials'))
      .then((res) => {
        result.resolve(res.body)
      })

    return result.promise
  }

  saveDocumentFields(podPath, frontMatter, locale) {
    const result = new Defer()
    const saveRequest = {
      'pod_path': podPath,
      'front_matter': frontMatter,
      'locale': locale,
    }

    console.log('save request', saveRequest)
    this.request.post(this.apiPath('editor/content'))
      .send(saveRequest)
      .then((res) => {
        result.resolve(res.body)
      })

    return result.promise
  }

  saveDocumentSource(podPath, rawFrontMatter) {
    const result = new Defer()
    const saveRequest = {
      'pod_path': podPath,
      'raw_front_matter': rawFrontMatter,
    }

    console.log('save request', saveRequest)
    this.request.post(this.apiPath('editor/content'))
      .send(saveRequest)
      .then((res) => {
        result.resolve(res.body)
      })

    return result.promise
  }
}
