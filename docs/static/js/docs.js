(function () {
  // 0. Mobile navigation drawer toggle.
  var navToggle = document.getElementById('nav-toggle');
  var navClose = document.getElementById('nav-close');
  var sidebar = document.getElementById('docs-sidebar');
  var backdrop = document.getElementById('sidebar-backdrop');

  function setDrawerOpen(open) {
    if (!sidebar || !backdrop || !navToggle) return;
    sidebar.classList.toggle('is-open', open);
    backdrop.hidden = !open;
    navToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    document.body.style.overflow = open ? 'hidden' : '';
  }

  if (navToggle && sidebar && backdrop) {
    navToggle.addEventListener('click', function () {
      setDrawerOpen(!sidebar.classList.contains('is-open'));
    });
    if (navClose) {
      navClose.addEventListener('click', function () { setDrawerOpen(false); });
    }
    backdrop.addEventListener('click', function () { setDrawerOpen(false); });
    sidebar.addEventListener('click', function (e) {
      if (e.target.closest && e.target.closest('a')) setDrawerOpen(false);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && sidebar.classList.contains('is-open')) {
        setDrawerOpen(false);
      }
    });
  }

  // 1. Build "On this page" table of contents from h2/h3 headings.
  var contentEl = document.querySelector('.docs-content');
  var tocList = document.getElementById('docs-toc');
  if (contentEl && tocList) {
    var headings = contentEl.querySelectorAll('h2, h3');
    if (headings.length === 0) {
      var tocAside = document.querySelector('.docs-toc');
      if (tocAside) tocAside.hidden = true;
    } else {
      headings.forEach(function (h) {
        if (!h.id) {
          h.id = h.textContent
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, '-')
            .replace(/(^-|-$)/g, '');
        }
        var li = document.createElement('li');
        li.className = h.tagName === 'H3' ? 'toc-item toc-item--sub' : 'toc-item';
        var a = document.createElement('a');
        a.href = '#' + h.id;
        a.textContent = h.textContent;
        li.appendChild(a);
        tocList.appendChild(li);
      });
    }
  }

  // 1b. Add zero-dependency Copy buttons to all code blocks.
  if (contentEl && navigator.clipboard) {
    contentEl.querySelectorAll('pre').forEach(function (pre) {
      var code = pre.querySelector('code');
      if (!code) return;
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'code-copy';
      btn.textContent = 'Copy';
      btn.setAttribute('aria-label', 'Copy code');
      btn.addEventListener('click', function () {
        navigator.clipboard.writeText(code.textContent || '').then(function () {
          btn.textContent = 'Copied';
          btn.classList.add('is-copied');
          setTimeout(function () {
            btn.textContent = 'Copy';
            btn.classList.remove('is-copied');
          }, 1600);
        });
      });
      pre.appendChild(btn);
    });
  }

  // 2. Zero-dependency client-side search over Grow's generated search index.
  var searchInput = document.getElementById('docs-search');
  var resultsEl = document.getElementById('docs-search-results');
  if (!searchInput || !resultsEl) return;

  var indexUrl = searchInput.getAttribute('data-index-url');
  var docsCache = null;

  function loadIndex() {
    if (docsCache) return Promise.resolve(docsCache);
    return fetch(indexUrl)
      .then(function (r) { return r.json(); })
      .then(function (data) {
        docsCache = data.docs || [];
        return docsCache;
      })
      .catch(function () { return []; });
  }

  function renderResults(matches) {
    resultsEl.textContent = '';
    if (!matches.length) {
      var empty = document.createElement('div');
      empty.className = 'search-empty';
      empty.textContent = 'No matching documentation pages.';
      resultsEl.appendChild(empty);
      resultsEl.hidden = false;
      return;
    }
    matches.slice(0, 8).forEach(function (item) {
      var a = document.createElement('a');
      a.className = 'search-result';
      a.href = item.location;

      var title = document.createElement('div');
      title.className = 'search-result__title';
      title.textContent = item.title;
      a.appendChild(title);

      if (item.snippet) {
        var snippet = document.createElement('div');
        snippet.className = 'search-result__snippet';
        snippet.textContent = item.snippet;
        a.appendChild(snippet);
      }
      resultsEl.appendChild(a);
    });
    resultsEl.hidden = false;
  }

  searchInput.addEventListener('input', function () {
    var query = (searchInput.value || '').trim().toLowerCase();
    if (query.length < 2) {
      resultsEl.hidden = true;
      return;
    }
    loadIndex().then(function (docs) {
      var terms = query.split(/\s+/).filter(Boolean);
      var scored = [];
      docs.forEach(function (d) {
        var title = (d.title || '').toLowerCase();
        var text = (d.text || '').toLowerCase();
        var score = 0;
        var allMatch = terms.every(function (t) {
          var inTitle = title.indexOf(t) !== -1;
          var inText = text.indexOf(t) !== -1;
          if (inTitle) score += 10;
          if (inText) score += 1;
          return inTitle || inText;
        });
        if (!allMatch) return;
        var pos = text.indexOf(terms[0]);
        var start = Math.max(0, pos - 40);
        var raw = (d.text || '').replace(/\s+/g, ' ').trim();
        var snippet = pos > -1 ? raw.slice(start, start + 140) : raw.slice(0, 140);
        if (start > 0) snippet = '…' + snippet;
        if (raw.length > start + 140) snippet += '…';
        scored.push({ location: d.location, title: d.title, snippet: snippet, score: score });
      });
      scored.sort(function (a, b) { return b.score - a.score; });
      renderResults(scored);
    });
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === '/' && document.activeElement !== searchInput && document.activeElement.tagName !== 'INPUT') {
      e.preventDefault();
      searchInput.focus();
    } else if (e.key === 'Escape') {
      resultsEl.hidden = true;
      searchInput.blur();
    }
  });

  document.addEventListener('click', function (e) {
    if (!resultsEl.contains(e.target) && e.target !== searchInput) {
      resultsEl.hidden = true;
    }
  });
})();
