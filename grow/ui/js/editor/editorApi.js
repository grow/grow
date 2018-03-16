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

    // TODO make request to server to get document.
    // this.request.get(...)
    result.resolve({
      'pod_path': '/content/pages/home.yaml',
      'fields': [
        {
          'type': 'text',
          'key': '$path',
          'label': 'Serving Path',
        },
        {
          'type': 'textarea',
          'key': 'meta.description',
          'label': 'Description',
        },
      ],
      'front_matter': {
        '$path': '/',
        'meta': {
          'description': 'Something really cool.',
        }
      },
      'serving_paths': {
        'en': '/',
      },
      'default_locale': 'en',
    })

    return result.promise
  }

  saveDocument(podPath, frontMatter, locale) {
    const result = new Defer()
    const saveRequest = {
      'pod_path': podPath,
      'front_matter': frontMatter,
      'locale': locale,
    }

    console.log('save request', saveRequest)

    // TODO make request to server to save document.
    // this.request.post(...)
    result.resolve({
      'pod_path': '/content/pages/home.yaml',
      'front_matter': {
        '$path': '/something',
        'meta': {
          'description': 'Something really really cool.',
        }
      },
      'serving_paths': {
        'en': '/',
      },
      'default_locale': 'en',
    })

    return result.promise
  }
}
