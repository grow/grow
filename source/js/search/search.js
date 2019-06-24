require.config({
  baseUrl: base_url
});

var SEARCH_PATH = 'text!../search_index-' + base_url_locale + '-json.html';

require([
  'mustache.min',
  'lunr.min',
  'text!search-results-template.mustache',
  SEARCH_PATH
], function (Mustache, lunr, results_template, data) {
  "use strict";

  function getSearchTerm() {
    var sPageURL = window.location.search.substring(1);
    var sURLVariables = sPageURL.split('&');
    for (var i = 0; i < sURLVariables.length; i++)
    {
      var sParameterName = sURLVariables[i].split('=');
      if (sParameterName[0] == 'q')
      {
        return decodeURIComponent(sParameterName[1].replace(/\+/g, '%20'));
      }
    }
  }

  var index = lunr(function () {
    this.field('title', {boost: 10});
    this.field('text');
    this.ref('location');
  });

  data = JSON.parse(data);
  var documents = {};

  for (var i=0; i < data.docs.length; i++) {
    var doc = data.docs[i];
    doc.location = doc.location;
    index.add(doc);
    documents[doc.location] = doc;
  }

  var search = function() {
    var query = document.getElementById('mkdocs-search-query').value;
    var search_results = document.getElementById("mkdocs-search-results");
    while (search_results.firstChild) {
      search_results.removeChild(search_results.firstChild);
    }

    if (query === '') {
      return;
    }

    var results = index.search(query);

    if (results.length > 0) {
      for (var i=0; i < results.length; i++) {
        var result = results[i];
        doc = documents[result.ref];
        doc.base_url = base_url;
        doc.summary = doc.text.substring(0, 200);
        var html = Mustache.to_html(results_template, doc);
        search_results.insertAdjacentHTML('beforeend', html);
      }
    } else {
      search_results.insertAdjacentHTML('beforeend', "<p>No results found</p>");
    }

    if (jQuery) {
      jQuery('#mkdocs_search_modal a').click(function(){
        jQuery('#mkdocs_search_modal').modal('hide');
      });
    }
  };

  var onKeyDown_ = function(e) {
    search();
  };

  var onKeyUp_ = function(e) {
  };

  var onFocus_ = function(e) {
  };

  var inputEl = document.getElementById('mkdocs-search-query');
  if (!inputEl) {
    return;
  }

  var term = getSearchTerm();
  if (term) {
    inputEl.value = term;
    search();
  }

  inputEl.addEventListener('keydown', onKeyDown_);
  inputEl.addEventListener('keyup', onKeyUp_);
  inputEl.addEventListener('focus', onFocus_);
});
