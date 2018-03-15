/**
 * Content editor.
 */

export default class Editor {
  constructor(containerEl) {
    this.containerEl = containerEl
    this.mobileToggleEl = this.containerEl.querySelector('#content_device')
    this.contentPreviewEl = this.containerEl.querySelector('.content__preview')

    this.mobileToggleEl.addEventListener('click', this.handleMobileClick.bind(this))
  }

  handleMobileClick() {
    if (this.mobileToggleEl.checked) {
      this.contentPreviewEl.classList.add('content__preview--mobile')
    } else {
      this.contentPreviewEl.classList.remove('content__preview--mobile')
    }
  }
}
