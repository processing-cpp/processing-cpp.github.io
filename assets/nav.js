(function() {
  // Prevent dark mode flash -- apply class before first paint
  try {
    if (localStorage.getItem('darkMode') === '1') document.documentElement.classList.add('dark-pre');
  } catch(e) {}
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
      <button id="nav-dark-btn" onclick="window.__toggleDark&&window.__toggleDark()" style="background:#111;color:#fff;border:none;padding:4px 12px;border-radius:4px;font-size:12px;cursor:pointer;margin-left:0.5rem;font-weight:600;">🌙 Dark</button>
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
      html.dark-pre body { background:#1a1a2e !important; }
      pre#code-pre { display:none !important; }
      .syntax-block { display:none !important; }
      .CodeMirror-scroll { border:none !important; background:transparent !important; }
      .CodeMirror-hscrollbar, .CodeMirror-vscrollbar { display:none !important; }

      pre#code-pre { display:none !important; }
      .syntax-block { display:none !important; }
      .CodeMirror-scroll { border:none !important; background:transparent !important; }
      .CodeMirror-hscrollbar, .CodeMirror-vscrollbar { display:none !important; }

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


  // CodeMirror syntax highlighting on reference/example pages
  if (document.querySelector('.syntax-block, .impl-block')) {
    const CDNJS = 'https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16';
    function loadScript(src, cb) {
      const s = document.createElement('script'); s.src = src;
      s.onload = cb; document.head.appendChild(s);
    }
    function loadLink(href) {
      const l = document.createElement('link');
      l.rel = 'stylesheet'; l.href = href;
      document.head.appendChild(l);
    }
    loadLink(CDNJS + '/codemirror.min.css');
    loadLink(SITE + '/assets/cppmode-theme.css');
    loadScript(CDNJS + '/codemirror.min.js', function() {
      loadScript(CDNJS + '/mode/clike/clike.min.js', function() {
        loadScript(SITE + '/assets/cppmode-keywords.js', function() {
          loadScript(SITE + '/assets/cppmode.js', function() {
            const dark = document.body.classList.contains('dark-mode');
            const allBlocks = document.querySelectorAll('.syntax-block, .impl-block');
            console.log('CM: found', allBlocks.length, 'blocks');
            allBlocks.forEach((el, i) => {
              console.log('block', i, 'tag:', el.tagName, 'class:', el.className, 'display:', getComputedStyle(el).display, 'content len:', el.textContent.trim().length);
            });
            console.log('CM wrappers already:', document.querySelectorAll('.cm-editor-wrap').length);
            console.log('CM instances already:', document.querySelectorAll('.CodeMirror').length);
            document.querySelectorAll('.CodeMirror').forEach((el,i) => {
              if(i < 3) console.log('CM', i, 'parent:', el.parentElement?.className, 'grandparent:', el.parentElement?.parentElement?.className);
            });
            if (document.querySelector('.cm-editor-wrap')) { console.log('GUARD: already rendered'); return; }
            console.log('content children:', Array.from(document.querySelector('.content')?.children||[]).map(el=>el.tagName+'.'+el.className).join(', '));
            document.querySelectorAll('.syntax-block, .impl-block').forEach(el => {
              el.style.cssText = 'display:none!important;visibility:hidden!important;height:0!important;overflow:hidden!important;';
              if (!el.parentNode) return;
              const code = el.textContent.trim();
              if (!code) return;
              const wrap = document.createElement('div');
              wrap.className = 'cm-editor-wrap';
              el.parentNode.insertBefore(wrap, el);
              const cm = CodeMirror(wrap, {
                value: code,
                mode: 'cppmode',
                theme: dark ? 'cppmode-dark' : 'cppmode',
                readOnly: true,
                lineNumbers: false,
                lineWrapping: false,
              });
              // Force full height - CM defaults to 300px
              const lineCount = cm.lineCount();
              const lineHeight = 18;
              const height = lineCount * lineHeight + 10;
              cm.setSize('100%', height + 'px');
            });
            // Switch theme on dark toggle
            document.querySelectorAll('.CodeMirror').forEach(el => {
              if (el.CodeMirror) el.CodeMirror.setOption('theme', dark ? 'cppmode-dark' : 'cppmode');
            });
          });
        });
      });
    });
  }

  // Dark mode via CSS class
  (function() {
    if (!document.getElementById('dark-mode-style')) {
      const style = document.createElement('style');
      style.id = 'dark-mode-style';
      style.textContent = `
        body.dark-mode { background:#1a1a2e !important; color:#cdd6f4 !important; }
        body.dark-mode p, body.dark-mode span:not([class*='cm-']), body.dark-mode h1, body.dark-mode h2, body.dark-mode h3, body.dark-mode h4, body.dark-mode li, body.dark-mode label, body.dark-mode td, body.dark-mode th { color:#cdd6f4 !important; }
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
        body.dark-mode .CodeMirror-gutters { background:#181825 !important; border-color:#313244 !important; }
        body.dark-mode #hero-preview, body.dark-mode #hero-preview iframe,
        body.dark-mode #logo-sketch-wrap, body.dark-mode #logo-sketch-wrap iframe { background:#1e1e2e !important; }
        body.dark-mode .CodeMirror-linenumber { color:#6c7086 !important; }
        body.dark-mode input, body.dark-mode select, body.dark-mode textarea { background:#181825 !important; color:#cdd6f4 !important; }
        body.dark-mode ::placeholder { color:#6c7086 !important; }
        /* Reference pages */
        body.dark-mode .content, body.dark-mode .ref-sidebar, body.dark-mode .sidebar-outer { background:#1e1e2e !important; }
        body.dark-mode .syntax-block { background:#181825 !important; color:#f8f8f2 !important; }
        body.dark-mode .impl-block { background:#0d0d0d !important; }
        body.dark-mode .returns-badge { background:#313244 !important; color:#cdd6f4 !important; }
        body.dark-mode .related-links a { background:#313244 !important; color:#cdd6f4 !important; }
        body.dark-mode .related-links a:hover { background:#45475a !important; }
        body.dark-mode .params-table th { color:#6c7086 !important; border-color:#313244 !important; }
        body.dark-mode .params-table td { border-color:#313244 !important; color:#cdd6f4 !important; }
        body.dark-mode .params-table td:first-child { color:#89b4fa !important; }
        body.dark-mode .params-table td:nth-child(2) { color:#a6e3a1 !important; }
        body.dark-mode .methods-table td { border-color:#313244 !important; color:#cdd6f4 !important; }
        body.dark-mode .methods-table td:first-child { color:#89b4fa !important; }
        body.dark-mode .ref-sidebar a { color:#a6adc8 !important; }
        body.dark-mode .ref-sidebar a:hover { background:#313244 !important; color:#cdd6f4 !important; }
        body.dark-mode .ref-sidebar a.active { background:#313244 !important; color:#cdd6f4 !important; }
        body.dark-mode .ref-cat-title { color:#cdd6f4 !important; }
        body.dark-mode .ref-subcat-title { color:#6c7086 !important; }
        body.dark-mode .cat-tag { color:#6c7086 !important; }
        body.dark-mode .content h2 { color:#6c7086 !important; }
        body.dark-mode .content p { color:#cdd6f4 !important; }
        body.dark-mode .topic-title { color:#cdd6f4 !important; border-color:#313244 !important; }
        body.dark-mode .fn-list a { color:#89b4fa !important; }
        body.dark-mode .fn-list a:hover { color:#cdd6f4 !important; }
        body.dark-mode footer { border-color:#313244 !important; color:#6c7086 !important; }
        /* Tutorials */
        body.dark-mode .tutorial-content, body.dark-mode .tutorial-body, body.dark-mode article { background:#1e1e2e !important; color:#cdd6f4 !important; }
        body.dark-mode .cm-static-wrap, body.dark-mode .code-block, body.dark-mode .highlight { background:#181825 !important; border-color:#313244 !important; }
        body.dark-mode blockquote { background:#181825 !important; border-color:#45475a !important; color:#a6adc8 !important; }
        body.dark-mode table { border-color:#313244 !important; }
        body.dark-mode table td, body.dark-mode table th { border-color:#313244 !important; color:#cdd6f4 !important; background:#1e1e2e !important; }
        body.dark-mode .sidebar-outer { background:#181825 !important; }
        body.dark-mode .note, body.dark-mode .warning, body.dark-mode .tip { background:#181825 !important; border-color:#45475a !important; color:#cdd6f4 !important; }
        /* Tutorials index */
        body.dark-mode .tutorial-card { background:#1e1e2e !important; border-color:#313244 !important; }
        body.dark-mode .tutorial-card:hover { background:#313244 !important; }
        body.dark-mode .tc-title { color:#89b4fa !important; }
        body.dark-mode .tc-desc { color:#a6adc8 !important; }
        body.dark-mode .tc-body { background:#181825 !important; border-color:#313244 !important; }
        body.dark-mode .tc-arrow { color:#6c7086 !important; }
        body.dark-mode .section-desc { color:#a6adc8 !important; }
        body.dark-mode .subtitle { color:#6c7086 !important; }
        body.dark-mode .help-box { background:#181825 !important; border-color:#313244 !important; color:#a6adc8 !important; }
        body.dark-mode .content { background:#1a1a2e !important; }
        body.dark-mode .layout { background:#1a1a2e !important; }
        body.dark-mode .path { color:#6c7086 !important; }
        /* Reference titles contrast */
        body.dark-mode .content h1 { color:#cdd6f4 !important; }
        body.dark-mode .content h2 { color:#89b4fa !important; }
        body.dark-mode .ref-sidebar a { color:#a6adc8 !important; }
        body.dark-mode .ref-cat-title { color:#cdd6f4 !important; }
        body.dark-mode .hero-link { color:#89b4fa !important; border-color:#89b4fa !important; }
        body.dark-mode .hero-link:hover { border-color:#cdd6f4 !important; color:#cdd6f4 !important; }
        body.dark-mode .hero-btn-download { background:#e8b400 !important; color:#111 !important; }
        body.dark-mode .hero-btn-editor { background:#4b9cd3 !important; color:#fff !important; }
      `;
      document.head.appendChild(style);
    }
    function applyDark(on) {
      document.body.classList.toggle('dark-mode', on);
      document.documentElement.classList.remove('dark-pre');
      const btn = document.getElementById('nav-dark-btn');
      if (btn) {
        btn.textContent = on ? '☀️ Light' : '🌙 Dark';
        btn.style.cssText = on
          ? 'background:#fff;color:#111;border:1px solid #555;padding:4px 12px;border-radius:4px;font-size:12px;cursor:pointer;margin-left:0.5rem;font-weight:600;'
          : 'background:#111;color:#fff;border:none;padding:4px 12px;border-radius:4px;font-size:12px;cursor:pointer;margin-left:0.5rem;font-weight:600;';
      }
      if (window.editor && window.editor.setOption)
        window.editor.setOption('theme', on ? 'cppmode-dark' : 'cppmode');
      // Switch static CodeMirror blocks theme
      document.querySelectorAll('.CodeMirror').forEach(el => {
        if (el.CodeMirror) el.CodeMirror.setOption('theme', on ? 'cppmode-dark' : 'cppmode');
      });
      // Tell sketch iframes about dark mode
      document.querySelectorAll('iframe').forEach(fr => {
        try { fr.contentWindow.postMessage(on ? 'dark' : 'light', '*'); } catch(e) {}
      });
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
