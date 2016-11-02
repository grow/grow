(function(grow){
  grow = grow || {};
  grow.ui = grow.ui || {};
  grow.ui.tools = grow.ui.tools || [];

  grow.ui.tools.push({
    'key': 'tool_ga_inspect',
    'name': 'GA Inspect',
    'button': {
      'events': {
        'click': function() {
          document.body.classList.toggle('grow__tool__ga--active');
        }
      }
    }
  });
})(grow || window.grow);
