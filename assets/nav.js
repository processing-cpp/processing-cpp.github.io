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
  // Dark mode via CSS class
  (function() {
    if (!document.getElementById('dark-mode-style')) {
      const style = document.createElement('style');
      style.id = 'dark-mode-style';
      style.textContent = `
        body.dark-mode { background:#1a1a2e !important; color:#cdd6f4 !important; }
        body.dark-mode * { color:#cdd6f4 !important; border-color:#313244 !important; background-color:transparent !important; }
        body.dark-mode a { color:#89b4fa !important; }
        body.dark-mode #site-nav { background:#181825 !important; border-color:#313244 !important; }
        body.dark-mode .sidebar, body.dark-mode #site-sidebar { background:#181825 !important; }
        body.dark-mode .pane-bar { background:#181825 !important; border-color:#313244 !important; }
        body.dark-mode .editor-pane, body.dark-mode .preview-pane { border-color:#313244 !important; }
        body.dark-mode .page-body, body.dark-mode .main, body.dark-mode .layout { background:#1a1a2e !important; }
        body.dark-mode .example-card, body.dark-mode .ref-card, body.dark-mode .examples-section { background:#1e1e2e !important; border-color:#313244 !important; }
        body.dark-mode pre, body.dark-mode code, body.dark-mode .cm-static-wrap { background:#181825 !important; border-color:#313244 !important; }
        body.dark-mode .btn-run { background:#e8b400 !important; color:#111 !important; }
        body.dark-mode .btn-stop { background:#313244 !important; color:#cdd6f4 !important; }
        body.dark-mode .nav-title-top, body.dark-mode .nav-title-bottom { color:#e8b400 !important; }
        body.dark-mode #nav-errors-link { color:#e8b400 !important; }
        body.dark-mode .sidebar a.active { color:#e8b400 !important; font-weight:700; }
        body.dark-mode #nav-dark-btn { background:#313244 !important; color:#cdd6f4 !important; border-color:#45475a !important; }
        body.dark-mode .CodeMirror { background:#1e1e2e !important; }
        body.dark-mode input, body.dark-mode select, body.dark-mode textarea { background:#181825 !important; color:#cdd6f4 !important; }
        body.dark-mode ::placeholder { color:#6c7086 !important; }
        body.dark-mode .hero-link { color:#89b4fa !important; border-color:#89b4fa !important; }
        body.dark-mode .hero-link:hover { border-color:#cdd6f4 !important; color:#cdd6f4 !important; }
        body.dark-mode .hero-btn-download { background:#e8b400 !important; color:#111 !important; }
        body.dark-mode .hero-btn-editor { background:#4b9cd3 !important; color:#fff !important; }
      `;
      document.head.appendChild(style);
    }
    function applyDark(on) {
      document.body.classList.toggle('dark-mode', on);
      const btn = document.getElementById('nav-dark-btn');
      if (btn) btn.textContent = on ? '☀️ Light' : '🌙 Dark';
      if (window.editor && window.editor.setOption)
        window.editor.setOption('theme', on ? 'cppmode-dark' : 'cppmode');
      try { localStorage.setItem('darkMode', on ? '1' : '0'); } catch(e) {}
    }
    window.__toggleDark = function() {
      applyDark(!document.body.classList.contains('dark-mode'));
    };
    try {
      if (localStorage.getItem('darkMode') === '1') applyDark(true);
    } catch(e) {}
  })();
})();
