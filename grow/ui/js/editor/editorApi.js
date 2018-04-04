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
      'editor': {
        'fields': [
          {
            'type': 'text',
            'key': '$path',
            'label': 'Serving Path',
          },
          {
            'type': 'text',
            'key': '$title',
            'label': 'Title',
          },
          {
            'type': 'textarea',
            'key': 'meta.description',
            'label': 'Description',
          },
          {
            'type': 'partials',
            'key': 'partials',
            'label': 'Partials',
          },
        ],
      },
      'front_matter': {
        '$title': 'Blinkk',
        '$path': '/',
        'meta': {
          'description': 'Something really cool.',
        },
        'partials': [
          {
            'partial': 'hero',
            'title': 'Blinkk',
            'subtitle': 'New to Blinkk?',
            'description': 'Great! This site is to help you get up to speed on how Blinkk works and some of the projects that we have going.',
            'cta': [
              {
                'title': 'Getting Started',
                'url': '!g.url "/content/pages/getting-started.yaml"',
              },
              {
                'title': 'Blinkk Projects',
                'url': '!g.url "/content/pages/projects.yaml"',
              },
            ],
          },
        ],
      },
      'serving_paths': {
        'en': '/',
      },
      'default_locale': 'en',
      'raw_front_matter': '$path: /\r$title: Something',
      'content': 'Something for content.',
    })

    return result.promise
  }

  getPartials(podPath) {
    const result = new Defer()

    // TODO make request to server to get partials.
    // this.request.get(...)
    result.resolve({
      'partials': {
        'hero': {
          'label': 'Hero',
          'editor': {
            'fields': [
              {
                'type': 'text',
                'key': 'title',
                'label': 'Hero Title',
              },
              {
                'type': 'text',
                'key': 'subtitle',
                'label': 'Hero Subtitle',
              },
              {
                'type': 'markdown',
                'key': 'description',
                'label': 'Description',
              },
            ],
          },
        },
      },
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

    // TODO make request to server to save document.
    // this.request.post(...)
    result.resolve({
      'pod_path': '/content/pages/home.yaml',
      'front_matter': {
        '$title': 'Blinkk Team',
        '$path': '/something',
        'meta': {
          'description': 'Something really really cool.',
        },
        'partials': [
          {
            'partial': 'hero',
            'title': 'Blinkk Hero',
            'subtitle': 'New to Blinkk saving?',
            'description': 'Great! This changes everything.',
            'cta': [
              {
                'title': 'Getting Started',
                'url': '!g.url "/content/pages/getting-started.yaml"',
              },
              {
                'title': 'Blinkk Projects',
                'url': '!g.url "/content/pages/projects.yaml"',
              },
            ],
          },
        ],
      },
      'raw_front_matter': '$path: /asdf\r$title: Other',
      'serving_paths': {
        'en': '/',
      },
      'default_locale': 'en',
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

    // TODO make request to server to save document.
    // this.request.post(...)
    result.resolve({
      'pod_path': '/content/pages/home.yaml',
      'front_matter': {
        '$title': 'Blinkk Team',
        '$path': '/something',
        'meta': {
          'description': 'Something really really cool.',
        },
        'partials': [
          {
            'partial': 'hero',
            'title': 'Blinkk Hero',
            'subtitle': 'New to Blinkk saving?',
            'description': 'Great! This changes everything.',
            'cta': [
              {
                'title': 'Getting Started',
                'url': '!g.url "/content/pages/getting-started.yaml"',
              },
              {
                'title': 'Blinkk Projects',
                'url': '!g.url "/content/pages/projects.yaml"',
              },
            ],
          },
        ],
      },
      'raw_front_matter': '$path: /asdf\r$title: Other',
      'serving_paths': {
        'en': '/',
      },
      'default_locale': 'en',
    })

    return result.promise
  }
}
