(function() {
  const path = window.location.pathname;
  const isRoot = path === '/' || path === '/index.html';
  const isOneLevelDeep = path.split('/').filter(Boolean).length === 1;
  const prefix = (isRoot || isOneLevelDeep) ? '/' : '../';

  const logoHref = isRoot ? null : prefix;

  const nav = document.getElementById('site-nav');
  const sidebar = document.getElementById('site-sidebar');

  if (nav) {
    nav.innerHTML = `
      <${logoHref ? `a href="${logoHref}"` : 'div'} class="nav-logo">
        <img src="${prefix}assets/cpp-logo.png" alt="C++ Mode">
        <span>C++ Mode</span>
      </${logoHref ? 'a' : 'div'}>
      <button class="hamburger" onclick="document.getElementById('site-sidebar').classList.toggle('open')">☰</button>
    `;
  }

  if (sidebar) {
    const links = [
      { href: `${prefix}libraries`, label: 'Libraries' },
      { href: `${prefix}reference`, label: 'Reference' },
      { href: `${prefix}examples`, label: 'Examples' },
      { href: `${prefix}about`, label: 'About' },
    ];
    sidebar.innerHTML = links.map(l => {
      const active = path.includes(l.label.toLowerCase()) ? 'class="active"' : '';
      return `<a href="${l.href}" ${active}>${l.label}</a>`;
    }).join('');
  }
})();
