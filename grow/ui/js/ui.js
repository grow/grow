var grow = grow || {};
grow.ui = grow.ui || {};
window.grow = grow;

grow.ui.main = function(settings) {
  if (!settings.injectEditUrl && !settings.injectTranslateUrl) {
    return;
  }
  var buttonsEl = document.createElement('div');
  buttonsEl.setAttribute('class', 'grow__buttons');
  if (settings.injectEditUrl) {
    var buttonEl = grow.ui.main.createButton_(
        'edit', settings.injectEditUrl);
    buttonsEl.appendChild(buttonEl);
  }
  if (settings.injectTranslateUrl) {
    var buttonEl = grow.ui.main.createButton_(
        'translate', settings.injectTranslateUrl);
    buttonsEl.appendChild(buttonEl);
  }
  var el = document.createElement('div');
  el.setAttribute('id', 'grow');
  el.appendChild(buttonsEl);
  document.body.appendChild(el);
};

grow.ui.main.createButton_ = function(kind, url) {
  var buttonEl = document.createElement('a');
  buttonEl.classList.add('grow__buttons__button');
  buttonEl.classList.add('grow__buttons__button--icon-' + kind);
  buttonEl.setAttribute('href', url);
  buttonEl.setAttribute('target', '_blank');
  return buttonEl;
};
