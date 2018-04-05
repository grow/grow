/**
 * Utility for working with apis.
 */

import Config from './config'

const request = require('superagent');

export default class Api {
  constructor(config) {
    this.config = new Config(config, {
      'basePath': '/_grow/api/',
    })
    this.request = request
  }

  apiPath(path) {
    return `${this.config.get('basePath', '/')}${path}`
  }
}
