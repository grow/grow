/**
 * Utility for working with apis.
 */

import Config from './config'

const request = require('superagent');

export default class Api {
  constructor(config) {
    this.config = new Config(config)
    this.request = request
  }
}
