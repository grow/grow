/**
 * Utility class for allowing a class to bind listeners and trigger callbacks.
 */

export default class Listeners {
  constructor() {
    this._listeners = {}
  }

  add(eventName, callback) {
    const listeners = this.listenersForEvent(eventName)
    listeners.push(callback)
  }

  listenersForEvent(eventName) {
    if (!this._listeners[eventName]) {
      this._listeners[eventName] = []
    }
    return this._listeners[eventName]
  }

  trigger(eventName, ...data) {
    for (const listener of this.listenersForEvent(eventName)) {
      listener(...data)
    }
  }
}
