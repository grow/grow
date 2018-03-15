/**
 * Throttle events using the requestAnimationFrame.
 */

export default class Throttle {
  constructor(type, name) {
    this.running = false;
    window.addEventListener(type, () => {
      if (this.running) {
        return
      }
      this.running = true
      requestAnimationFrame(() => {
        window.dispatchEvent(new CustomEvent(name))
        this.running = false;
      })
    })
  }
}
