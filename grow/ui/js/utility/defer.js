export default class Defer {
  constructor() {
    this.resolve = null
    this.reject = null

    this.promise = new Promise(function(resolve, reject) {
      this.resolve = resolve
      this.reject = reject
    }.bind(this))

    Object.freeze(this)
  }
}
