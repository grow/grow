var grow = grow || {};
grow.ui = grow.ui || {};
window.grow = grow;

grow.ui.main = function(settings) {
  var buttonEl;
  var buttonsEl = document.createElement('div');
  buttonsEl.setAttribute('class', 'buttons');
  buttonsEl.addEventListener('mouseover', function() {
    buttonsEl.classList.add('expand');
  });
  buttonsEl.addEventListener('mouseout', function() {
    buttonsEl.classList.remove('expand');
  });

  if (settings.injectEditUrl) {
    buttonsEl.appendChild(
      grow.ui.main.createButton_('edit', settings.injectEditUrl));
  }

  if (settings.injectTranslateUrl) {
    buttonsEl.appendChild(grow.ui.main.createButton_(
      'translate', settings.injectTranslateUrl));
  }

  buttonsEl.appendChild(grow.ui.main.createButton_('primary', null, {
    'click': function() {
      buttonsEl.classList.toggle('expand');
    }
  }));

  var el = document.createElement('div');
  el.setAttribute('id', 'grow-utils');
  el.appendChild(buttonsEl);
  document.body.appendChild(el);
};

grow.ui.main.createButton_ = function(kind, url, events) {
  var buttonEl = document.createElement('a');
  buttonEl.classList.add('button');
  buttonEl.classList.add('icon_' + kind);

  if (url) {
    buttonEl.setAttribute('href', url);
    buttonEl.setAttribute('target', '_blank');
  }

  if (events) {
    for (var prop in events) {
      buttonEl.addEventListener(prop, events[prop]);
    }
  }

  return buttonEl;
};
