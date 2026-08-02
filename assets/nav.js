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
})();
