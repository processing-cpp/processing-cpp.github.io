(function() {
  const path = window.location.pathname;

  // Figure out prefix based on depth
  const parts = path.replace(/\/$/, '').split('/').filter(Boolean);
  const isRoot = parts.length === 0;
  const isExamplePage = parts.length === 2 && parts[0] === 'examples';
  const prefix = (isRoot) ? '/' : '../';

  // Active link detection
  function isActive(name) {
    return path.includes('/' + name);
  }

  function link(name, label) {
    const active = isActive(name) ? ' class="active"' : '';
    return `<a href="${prefix}${name}"${active}>${label}</a>`;
  }

  // Inject nav
  const nav = document.getElementById('site-nav');
  if (nav) {
    const logoTag = isRoot
      ? `<div class="nav-logo">`
      : `<a href="${prefix}" class="nav-logo">`;
    const logoClose = isRoot ? `</div>` : `</a>`;
    nav.innerHTML = `
      ${logoTag}
        <img src="${prefix}assets/cpp-logo.png" alt="C++ Mode">
        <span>C++ Mode</span>
      ${logoClose}
      <button class="hamburger" onclick="document.querySelector('.sidebar-outer').classList.toggle('open')">☰</button>
    `;
  }

  // Inject sidebar top links
  const sidebar = document.getElementById('site-sidebar');
  if (sidebar) {
    sidebar.innerHTML = `
      ${link('libraries', 'Libraries')}
      ${link('reference', 'Reference')}
      ${link('examples', 'Examples')}
      ${link('about', 'About')}
    `;
  }
})();
