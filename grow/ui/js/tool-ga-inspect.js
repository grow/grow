(function(grow){
  grow = grow || {};
  grow.ui = grow.ui || {};
  grow.ui.tools = grow.ui.tools || [];

  if (!document.querySelector('[data-g-event]')) {
    return;
  }

  var messageContainer = document.createElement('div');
  var hasInitialized = false;
  var isActive = false;
  var dataOrder = ['gEvent', 'gLabel', 'gAction'];
  var dataRegex = /^g[A-Z].*/;

  var formatDataItem = function(title, value) {
    var container = document.createElement('div');
    var header = document.createElement('h2');
    var content = document.createElement('p');

    header.appendChild(document.createTextNode(title));
    container.appendChild(header);
    content.appendChild(document.createTextNode(value));
    container.appendChild(content);

    return container;
  }

  var formatData = function(data) {
    var container = document.createElement('div');

    while (messageContainer.firstChild) {
      messageContainer.removeChild(messageContainer.firstChild);
    }

    dataOrder.forEach(function(key) {
      if (data[key]) {
        container.appendChild(formatDataItem(key.substr(1), data[key]))
      }
    });

    for (var key in data) {
      if (data.hasOwnProperty(key)
          && dataRegex.test(key)
          && !dataOrder.includes(key)) {
        container.appendChild(formatDataItem(key.substr(1), data[key]))
      }
    }

    messageContainer.appendChild(container);
  };

  var onMouseOver = function(e) {
    var target = e.target;

    // Get the closet target with the correct data elements.
    while (target && !target.getAttribute('data-g-event')) {
      target = target.parentNode;
    }

    if (!target) {
      console.error('Cannot find matching target for analytics highlighting.');
      return;
    }

    var data = target.dataset;

    // SVG does not have the dataset, so mock a basic one.
    if (!data) {
      data = {
        gEvent: target.getAttribute('data-g-event'),
        gLabel: target.getAttribute('data-g-label'),
        gAction: target.getAttribute('data-g-action')
      };
    }

    formatData(data);
  };

  var triggerTool = function() {
    document.body.classList.toggle('grow_tool__ga--active');
    isActive = !isActive;

    if (!hasInitialized) {
      messageContainer.classList.add('grow_tool__ga__popup');

      var elements = document.querySelectorAll('[data-g-event]');
      elements.forEach(function(element) {
        element.addEventListener("mouseover", onMouseOver);
      });

      document.body.appendChild(messageContainer);
      hasInitialized = true;
    }
  };

  grow.ui.tools.push({
    'key': 'tool_ga_inspect',
    'name': 'GA Inspect',
    'button': {
      'events': {
        'click': triggerTool
      }
    }
  });
})(grow || window.grow);
