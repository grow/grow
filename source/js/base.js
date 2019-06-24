$(document).ready(function() {
  createSideNavigation();
  initSearchField();
});


function createSideNavigation() {
  var toc = document.querySelector('.bs-sidetoc');
  var main = document.querySelector('[role=main]');
  var headlines = main.querySelectorAll('h2');
  var els = headlines.length ? headlines : main.querySelectorAll('h4');
  [].forEach.call(els, function(el) {
    var li = document.createElement('li');
    var a = document.createElement('a');
    a.href = '#' + el.id;
    a.textContent = el.textContent.trim();
    li.appendChild(a);
    toc.appendChild(li);
  });
  if (els.length) {
    toc.removeAttribute('hidden');
  }

  $('body').scrollspy({
    target: '.sidetoc',
    offset: 20
  });
};


function initSearchField() {
  $('input[type=search]').on('search', function () {
    if ($(this).val() == '') {
      $('#mkdocs-search-results').empty();
      $(this).blur();
    }
  });

  $('html').click(function() {
    if ($('#mkdocs-search-query').is(':focus') &&
        $('#mkdocs-search-query').val() != '' ) {
      return;
    }

    if(!$('#mkdocs-search-results').is(':empty')) {
      $('#mkdocs-search-results').empty();
    }
  });

  $('#mkdocs-search-results').click(function(event) {
    event.stopPropagation();
  });
};
