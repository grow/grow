/**
 * Utility for working with deep object references.
 *
 * Example: obj.get('somthing.sub.key') would deeply reference the object.
 */

export default class DeepObject {
  constructor(obj) {
    this._obj = obj || {}
  }

  get(key) {
    let root = this._obj
    for (const part of key.split('.')) {
      if (!part in root) {
        return undefined
      }
      root = root[part]
    }
    return root
  }
}
