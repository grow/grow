var grow = grow || {};
grow.ui = grow.ui || {};
window.grow = grow;

grow.ui.main = function(settings) {
  if (!settings.injectEditUrl) {
    return;
  }
  var buttonsEl = document.createElement('div');
  buttonsEl.setAttribute('class', 'grow__buttons');
  var buttonEl = document.createElement('a');
  buttonEl.classList.add('grow__buttons__button');
  buttonEl.classList.add('grow__buttons__button--icon-edit');
  buttonEl.setAttribute('href', settings.injectEditUrl);
  buttonEl.setAttribute('target', '_blank');
  buttonsEl.appendChild(buttonEl);
  var el = document.createElement('div');
  el.setAttribute('id', 'grow');
  el.appendChild(buttonsEl);
  document.body.appendChild(el);
};
