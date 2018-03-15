/**
 * Utility for working with config.
 */

export default class Config {
  constructor(config, defaultValues) {
    this._defaultValues = defaultValues || {}
    this._config = Object.assign({}, this._defaultValues, config || {})

    // Allow for direct access to config values.
    for (const key of Object.keys(this._config)) {
      this[key] = this._config[key]
    }
  }

  get(key, defaultValue) {
    if (typeof this._config[key] == 'undefined') {
      return defaultValue
    }
    return this._config[key]
  }

  set(key, value) {
    this._config[key] = value
    return this[key] = value
  }
}
