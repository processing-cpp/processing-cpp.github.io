(function() {
  const SITE = 'https://processing-cpp.github.io';
  const path = window.location.pathname;
  const parts = path.replace(/\/$/, '').split('/').filter(Boolean);
  const isRoot = parts.length === 0 || (parts.length === 1 && parts[0] === 'index.html');
  // Depth = number of directory levels below site root. A trailing
  // "index.html" or "<file>.html" segment doesn't count as a directory level.
  const hasTrailingFile = parts.length > 0 && parts[parts.length - 1].endsWith('.html');
  const depth = isRoot ? 0 : (hasTrailingFile ? parts.length - 1 : parts.length);
  const prefix = depth === 0 ? '/' : '../'.repeat(depth);

  function isActive(name) { return path.includes('/' + name); }

  function link(href, label, style, activeKey) {
    const active = isActive(activeKey || href) ? ' class="active"' : '';
    const s = style ? ` style="${style}"` : '';
    return `<a href="${prefix}${href}"${active}${s}>${label}</a>`;
  }

  const nav = document.getElementById('site-nav');
  if (nav) {
    nav.innerHTML = `
      <a href="${SITE}" class="nav-logo">
        <img src="${prefix}assets/cpp-logo.png" alt="Processing for C++">
        <div class="nav-title">
          <span class="nav-title-top">Processing</span>
          <span class="nav-title-bottom">C++</span>
        </div>
      </a>
      <button class="hamburger" style="display:${window.NAV_NO_HAMBURGER?"none":""}" style="display:none" onclick="
        var s = document.querySelector('.sidebar-outer, .sidebar');
        if(s) s.classList.toggle('open');
      ">☰</button>
      <a href="${prefix}error/index.html" id="nav-errors-link"${isActive('error') ? ' class="active"' : ''}>Errors</a>
      <button id="nav-dark-btn" onclick="window.__toggleDark&&window.__toggleDark()" style="background:none;border:1px solid #e0e0e0;color:#555;padding:3px 10px;border-radius:4px;font-size:12px;cursor:pointer;margin-left:0.5rem;">🌙</button>
    `;
  }

  const sidebar = document.getElementById('site-sidebar') || document.querySelector('.sidebar');
  if (sidebar) {
    sidebar.innerHTML = `
      ${link('whats-new', "What's New", 'color:#e8b400;font-weight:700;')}
      <div style="height:1px;background:#e0e0e0;margin:0.5rem 0;"></div>
      ${link('libraries', 'Libraries')}
      ${link('downloads', 'Downloads')}
      ${link('tutorials', 'Tutorials')}
      ${link('reference', 'Reference')}
      ${link('examples', 'Examples')}
      ${link('editor', 'Editor')}
      ${link('about', 'About')}
      <a href="https://discord.gg/Un3DFmrUje" target="_blank" style="color:#5865F2;font-weight:600;">Discord</a>
    `;
  }

  if (!document.getElementById('nav-shared-style')) {
    const style = document.createElement('style');
    style.id = 'nav-shared-style';
    style.textContent = `
      #site-nav {
        border-bottom: 1px solid #e0e0e0;
        padding: 0 2rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        height: 60px;
        position: sticky;
        top: 0;
        background: #fff;
        z-index: 100;
      }
      .nav-logo { display: flex; align-items: center; gap: 10px; text-decoration: none; }
      .nav-logo img { width: 28px; height: 28px; }
      .nav-title { display: flex; flex-direction: column; line-height: 1.15; }
      .nav-title-top  { font-size: 14px; font-weight: 700; color: #e8b400; }
      .nav-title-bottom { font-size: 14px; font-weight: 700; color: #e8b400; }
      #nav-errors-link { margin-left: auto; font-size: 14px; font-weight: 700; color: #e8b400; text-decoration: none; }
      #nav-errors-link:hover { color: #c99700; }
      .hamburger { background: none; border: none; cursor: pointer; font-size: 22px; padding: 4px 8px; display: none; margin-left: 0.5rem; }
      @media (max-width: 768px) { .hamburger { display: block; } }
    `;
    document.head.appendChild(style);
  }

  if (!document.getElementById('search-wrap')) {
    const s = document.createElement('script');
    s.src = SITE + '/assets/search.js';
    document.head.appendChild(s);
  }
  // Dark mode
  (function() {
    const DARK = {
      body: 'background:#1a1a2e;color:#e0e0e0',
      nav: 'background:#16213e;border-color:#0f3460',
      sidebar: 'background:#16213e;border-color:#0f3460',
    };
    function applyDark(on) {
      document.body.setAttribute('data-dark', on ? '1' : '');
      const btn = document.getElementById('nav-dark-btn');
      if (btn) {
        btn.textContent = on ? '☀️' : '🌙';
        btn.style.background = on ? '#16213e' : '#111';
        btn.style.color = on ? '#e0e0e0' : '#fff';
        btn.style.borderColor = on ? '#0f3460' : '#333';
      }
      const nav = document.getElementById('site-nav');
      const sb = document.getElementById('site-sidebar') || document.querySelector('.sidebar');
      if (nav) { nav.style.background = on ? '#16213e' : ''; nav.style.borderColor = on ? '#0f3460' : ''; nav.style.color = on ? '#e0e0e0' : ''; }
      if (sb) { sb.style.background = on ? '#16213e' : ''; sb.style.color = on ? '#e0e0e0' : ''; }
      // Make all links and muted text visible
      document.querySelectorAll('a, .sidebar a, #site-nav a, p, span, h1, h2, h3, li, label').forEach(el => {
        if (on) { if (!el.style.color || el.style.color === 'rgb(170, 170, 170)' || el.style.color === '#aaa') el.style.color = '#e0e0e0'; }
        else { el.style.color = ''; }
      });
      document.body.style.background = on ? '#1a1a2e' : '';
      document.body.style.color = on ? '#e0e0e0' : '';
      // Editor-specific: pane bars
      document.querySelectorAll('.pane-bar, .editor-pane, .preview-pane').forEach(el => {
        el.style.background = on ? '#16213e' : '';
        el.style.borderColor = on ? '#0f3460' : '';
        el.style.color = on ? '#e0e0e0' : '';
      });
      try { localStorage.setItem('darkMode', on ? '1' : '0'); } catch(e) {}
    }
    window.__toggleDark = function() {
      const on = document.body.getAttribute('data-dark') !== '1';
      applyDark(on);
      // Also update CodeMirror if on editor page
      if (window.editor && window.editor.setOption) {
        window.editor.setOption('theme', on ? 'cppmode-dark' : 'cppmode');
      }
    };
    // Restore preference
    try {
      if (localStorage.getItem('darkMode') === '1') applyDark(true);
    } catch(e) {}
  })();
})();
