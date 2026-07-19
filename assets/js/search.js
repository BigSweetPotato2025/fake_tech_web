(function () {
  'use strict';

  var SearchManager = function () {
    this.index = null;
    this.indexLoaded = false;
    this.searchInputs = [];
    this.resultsContainer = null;
    this.activeIndex = -1;
    this.debounceTimer = null;
    this.init();
  };

  SearchManager.prototype.init = function () {
    var self = this;
    this.searchInputs = document.querySelectorAll('.search-input');
    if (this.searchInputs.length === 0) return;

    this.resultsContainer = document.createElement('div');
    this.resultsContainer.className = 'search-dropdown hidden';
    this.resultsContainer.setAttribute('role', 'listbox');
    this.searchInputs[0].parentElement.style.position = 'relative';
    this.searchInputs[0].parentElement.appendChild(this.resultsContainer);

    this.searchInputs.forEach(function (input) {
      input.setAttribute('autocomplete', 'off');
      input.setAttribute('role', 'combobox');
      input.setAttribute('aria-expanded', 'false');
      input.setAttribute('aria-autocomplete', 'list');

      input.addEventListener('input', function (e) {
        var query = e.target.value.trim();
        self.debounceSearch(query);
      });

      input.addEventListener('focus', function () {
        if (self.indexLoaded && this.value.trim()) {
          self.resultsContainer.classList.remove('hidden');
        }
      });

      input.addEventListener('keydown', function (e) {
        self.handleKeydown(e);
      });
    });

    document.addEventListener('click', function (e) {
      var container = self.searchInputs[0].parentElement;
      if (!container.contains(e.target)) {
        self.resultsContainer.classList.add('hidden');
        self.searchInputs.forEach(function (inp) {
          inp.setAttribute('aria-expanded', 'false');
        });
      }
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        self.resultsContainer.classList.add('hidden');
        self.searchInputs.forEach(function (inp) {
          inp.setAttribute('aria-expanded', 'false');
        });
      }
    });

    this.loadIndex();
  };

  SearchManager.prototype.loadIndex = function () {
    var self = this;
    if (this.indexLoaded) return;

    fetch('/json/search.json')
      .then(function (res) {
        if (!res.ok) throw new Error('Search index not found');
        return res.json();
      })
      .then(function (data) {
        self.index = data;
        self.indexLoaded = true;
      })
      .catch(function () {
        self.indexLoaded = false;
      });
  };

  SearchManager.prototype.debounceSearch = function (query) {
    var self = this;
    clearTimeout(this.debounceTimer);
    if (query.length < 1) {
      this.resultsContainer.classList.add('hidden');
      return;
    }
    this.debounceTimer = setTimeout(function () {
      self.executeSearch(query);
    }, 300);
  };

  SearchManager.prototype.executeSearch = function (query) {
    if (!this.indexLoaded || !this.index) return;

    var q = query.toLowerCase();
    var results = [];
    var seen = {};

    for (var i = 0; i < this.index.length; i++) {
      var item = this.index[i];
      if (results.length >= 20) break;

      var name = (item.name || '').toLowerCase();
      var owner = (item.owner || '').toLowerCase();
      var desc = (item.description || '').toLowerCase();
      var topics = (item.topics || []).join(' ').toLowerCase();
      var fullName = (item.full_name || '').toLowerCase();

      var score = 0;
      if (fullName === q) score = 100;
      else if (fullName.indexOf(q) !== -1) score = 80;
      else if (name.indexOf(q) !== -1) score = 70;
      else if (owner.indexOf(q) !== -1) score = 50;
      else if (desc.indexOf(q) !== -1) score = 30;
      else if (topics.indexOf(q) !== -1) score = 20;

      if (score > 0 && !seen[item.full_name]) {
        seen[item.full_name] = true;
        results.push({ item: item, score: score });
      }
    }

    results.sort(function (a, b) { return b.score - a.score; });
    this.renderResults(results.map(function (r) { return r.item; }));
  };

  SearchManager.prototype.renderResults = function (results) {
    var container = this.resultsContainer;
    container.innerHTML = '';

    if (results.length === 0) {
      container.innerHTML = '<div class="px-4 py-6 text-center text-sm text-gray-500">No projects found</div>';
      container.classList.remove('hidden');
      return;
    }

    var list = document.createElement('div');
    results.forEach(function (item, idx) {
      var el = document.createElement('a');
      el.href = '/projects/' + item.full_name + '/';
      el.className = 'search-result-item';
      el.setAttribute('role', 'option');
      el.setAttribute('data-index', idx);

      var stars = item.stars >= 1000
        ? (item.stars / 1000).toFixed(1) + 'k'
        : item.stars;

      el.innerHTML =
        '<div class="flex items-center justify-between">' +
          '<div class="flex-1 min-w-0">' +
            '<div class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">' +
              (item.full_name || '') +
            '</div>' +
            (item.description
              ? '<div class="text-xs text-gray-500 dark:text-gray-400 truncate mt-0.5">' +
                self.escapeHtml(item.description) +
              '</div>'
              : '') +
          '</div>' +
          '<div class="flex items-center gap-3 ml-3 flex-shrink-0">' +
            (item.language
              ? '<span class="text-xs text-gray-400 dark:text-gray-500">' +
                self.escapeHtml(item.language) +
              '</span>'
              : '') +
            '<span class="text-xs text-gray-400 dark:text-gray-500">' +
              '<svg class="w-3.5 h-3.5 inline-block mr-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"/></svg>' +
              stars +
            '</span>' +
          '</div>' +
        '</div>';

      el.addEventListener('mousedown', function (e) {
        e.preventDefault();
        window.location.href = this.href;
      });

      el.addEventListener('mouseenter', function () {
        var active = container.querySelector('.active');
        if (active) active.classList.remove('active');
        this.classList.add('active');
      });

      list.appendChild(el);
    });

    container.appendChild(list);
    container.classList.remove('hidden');

    this.searchInputs.forEach(function (inp) {
      inp.setAttribute('aria-expanded', 'true');
    });
  };

  SearchManager.prototype.escapeHtml = function (text) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
  };

  SearchManager.prototype.handleKeydown = function (e) {
    var items = this.resultsContainer.querySelectorAll('.search-result-item');
    if (items.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        this.activeIndex = Math.min(this.activeIndex + 1, items.length - 1);
        this.highlightItem(items);
        break;
      case 'ArrowUp':
        e.preventDefault();
        this.activeIndex = Math.max(this.activeIndex - 1, 0);
        this.highlightItem(items);
        break;
      case 'Enter':
        e.preventDefault();
        if (this.activeIndex >= 0 && items[this.activeIndex]) {
          window.location.href = items[this.activeIndex].href;
        }
        break;
    }
  };

  SearchManager.prototype.highlightItem = function (items) {
    items.forEach(function (el, idx) {
      el.classList.toggle('active', idx === this.activeIndex);
    }, this);

    if (items[this.activeIndex]) {
      items[this.activeIndex].scrollIntoView({ block: 'nearest' });
    }
  };

  var self = this;
  document.addEventListener('DOMContentLoaded', function () {
    new SearchManager();
  });
})();
