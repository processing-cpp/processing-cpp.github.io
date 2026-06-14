(function() {
  const SITE = 'https://processing-cpp.github.io';
  const path = window.location.pathname;
  const parts = path.replace(/\/$/, '').split('/').filter(Boolean);
  const isRoot = parts.length === 0 || (parts.length === 1 && parts[0] === 'index.html');
  const prefix = isRoot ? '/' : '../';

  function isActive(name) { return path.includes('/' + name); }
  function link(name, label) {
    const active = isActive(name) ? ' class="active"' : '';
    return `<a href="${prefix}${name}"${active}>${label}</a>`;
  }

  const logoHTML = `
    <img src="${prefix}assets/cpp-logo.png" alt="C++ Mode">
    <div class="nav-title">
      <span class="nav-title-top">Processing</span>
      <span class="nav-title-bottom">C++</span>
    </div>
  `;

  const nav = document.getElementById('site-nav');
  if (nav) {
    const logoWrap = isRoot
      ? `<div class="nav-logo">${logoHTML}</div>`
      : `<a href="${prefix}" class="nav-logo">${logoHTML}</a>`;
    nav.innerHTML = `
      ${logoWrap}
      <button class="hamburger" onclick="
        document.querySelector('.sidebar-outer, .sidebar') &&
        document.querySelector('.sidebar-outer, .sidebar').classList.toggle('open')
      ">☰</button>
    `;
  }

  // Inject sidebar links into both #site-sidebar and .sidebar (main page)
  const sidebar = document.getElementById('site-sidebar') || document.querySelector('.sidebar');
  if (sidebar) {
    sidebar.innerHTML = `
      ${link('libraries', 'Libraries')}
      ${link('reference', 'Reference')}
      ${link('examples', 'Examples')}
      ${link('about', 'About')}
    `;
  }

  // Inject shared nav styles
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
      .nav-logo {
        display: flex;
        align-items: center;
        gap: 10px;
        color: #111;
        text-decoration: none;
      }
      .nav-logo img { width: 28px; height: 28px; }
      .nav-title {
        display: flex;
        flex-direction: column;
        line-height: 1.1;
      }
      .nav-title-top {
        font-size: 13px;
        font-weight: 600;
        color: #111;
      }
      .nav-title-bottom {
        font-size: 13px;
        font-weight: 700;
        color: #e8b400;
      }
      .hamburger {
        background: none;
        border: none;
        cursor: pointer;
        font-size: 22px;
        padding: 4px 8px;
        display: none;
        margin-left: 0.5rem;
      }
      @media (max-width: 768px) {
        .hamburger { display: block; }
      }
    `;
    document.head.appendChild(style);
  }

  // Load search via absolute URL
  if (!document.getElementById('search-wrap')) {
    const s = document.createElement('script');
    s.src = SITE + '/assets/search.js';
    document.head.appendChild(s);
  }
})();
