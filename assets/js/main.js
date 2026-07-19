(function () {
  'use strict';

  function initTheme() {
    var stored = localStorage.getItem('theme');
    var html = document.documentElement;
    if (stored) {
      html.classList.toggle('dark', stored === 'dark');
    } else {
      var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      html.classList.toggle('dark', prefersDark);
    }
  }

  function toggleTheme() {
    var html = document.documentElement;
    var isDark = html.classList.toggle('dark');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    updateToggleIcon(isDark);
  }

  function updateToggleIcon(isDark) {
    var toggles = document.querySelectorAll('.theme-toggle');
    toggles.forEach(function (btn) {
      btn.innerHTML = isDark
        ? '<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg>'
        : '<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/></svg>';
    });
  }

  function initMobileNav() {
    var btn = document.querySelector('.mobile-nav-toggle');
    var menu = document.querySelector('.mobile-nav');
    if (!btn || !menu) return;

    btn.addEventListener('click', function () {
      var expanded = btn.getAttribute('aria-expanded') === 'true' ? false : true;
      btn.setAttribute('aria-expanded', expanded);
      menu.classList.toggle('hidden', !expanded);
    });

    document.addEventListener('click', function (e) {
      if (!btn.contains(e.target) && !menu.contains(e.target)) {
        btn.setAttribute('aria-expanded', 'false');
        menu.classList.add('hidden');
      }
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        btn.setAttribute('aria-expanded', 'false');
        menu.classList.add('hidden');
      }
    });
  }

  function initCopyButtons() {
    document.querySelectorAll('pre').forEach(function (pre) {
      var code = pre.querySelector('code');
      if (!code || !code.textContent.trim()) return;

      var btn = document.createElement('button');
      btn.className = 'absolute top-2 right-2 px-2 py-1 text-xs rounded bg-gray-700 hover:bg-gray-600 text-gray-200 transition-colors';
      btn.textContent = 'Copy';
      btn.setAttribute('aria-label', 'Copy code to clipboard');
      pre.style.position = 'relative';
      pre.appendChild(btn);

      btn.addEventListener('click', function () {
        var text = code.textContent;
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).then(function () {
            btn.textContent = 'Copied!';
            setTimeout(function () { btn.textContent = 'Copy'; }, 2000);
          });
        } else {
          var ta = document.createElement('textarea');
          ta.value = text;
          ta.style.position = 'fixed';
          ta.style.opacity = '0';
          document.body.appendChild(ta);
          ta.select();
          document.execCommand('copy');
          document.body.removeChild(ta);
          btn.textContent = 'Copied!';
          setTimeout(function () { btn.textContent = 'Copy'; }, 2000);
        }
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initTheme();

    var themeToggles = document.querySelectorAll('.theme-toggle');
    themeToggles.forEach(function (btn) {
      btn.addEventListener('click', toggleTheme);
    });

    var isDark = document.documentElement.classList.contains('dark');
    updateToggleIcon(isDark);

    initMobileNav();
    initCopyButtons();
  });
})();
