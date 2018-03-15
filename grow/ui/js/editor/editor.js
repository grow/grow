/**
 * Content editor.
 */

export default class Editor {
  constructor(containerEl) {
    this.containerEl = containerEl
    this.mobileToggleEl = this.containerEl.querySelector('.content__device')
    this.contentPreviewEl = this.containerEl.querySelector('.content__preview')

    this.mobileToggleEl.addEventListener('click', this.handleMobileClick.bind(this))
  }

  handleMobileClick() {
    this.contentPreviewEl.classList.toggle('content__preview--mobile')
  }
}
