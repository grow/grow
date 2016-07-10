var grow = grow || {};
grow.ui = grow.ui || {};


grow.ui.main = function() {
  var buttonsEl = document.createElement('div');
  buttonsEl.setAttribute('class', 'grow__buttons');
  var buttonEl = document.createElement('div');
  buttonEl.setAttribute('class', 'grow__buttons__button');
  buttonsEl.appendChild(buttonEl);
  var el = document.createElement('div');
  el.setAttribute('id', 'grow');
  el.appendChild(buttonsEl);
  document.body.appendChild(el);
};


grow.ui.main();
