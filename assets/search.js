(function() {
  const SITE = 'https://processing-cpp.github.io';

  function injectSearch() {
    const nav = document.getElementById('site-nav');
    if (!nav) return;
    if (document.getElementById('search-wrap')) return; // already injected

    const wrap = document.createElement('div');
    wrap.id = 'search-wrap';
    wrap.innerHTML = `
      <div id="search-box">
        <input id="search-input" type="text" placeholder="Search reference…" autocomplete="off" spellcheck="false">
        <div id="search-results" hidden></div>
      </div>
    `;
    nav.appendChild(wrap);

    const style = document.createElement('style');
    style.textContent = `
      #search-wrap { position: relative; margin-left: auto; padding-right: 1rem; }
      #search-input {
        width: 220px; padding: 6px 12px;
        border: 1px solid #e0e0e0; border-radius: 20px;
        font-size: 13px; font-family: inherit;
        background: #f8f8f8; outline: none;
        transition: border-color 0.15s, width 0.2s;
      }
      #search-input:focus { border-color: #aaa; background: #fff; width: 280px; }
      #search-results {
        position: absolute; top: calc(100% + 8px); right: 0;
        width: 360px; background: #fff;
        border: 1px solid #e0e0e0; border-radius: 8px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.1);
        max-height: 400px; overflow-y: auto; z-index: 9999;
      }
      .sr { display: block; padding: 10px 14px; border-bottom: 1px solid #f0f0f0; text-decoration: none; color: #111; }
      .sr:last-child { border-bottom: none; }
      .sr:hover, .sr:focus { background: #f8f8f8; outline: none; }
      .sr-name { font-family: "SF Mono","Fira Code",monospace; font-size: 13px; font-weight: 600; }
      .sr-name mark { background: #fff3b0; border-radius: 2px; padding: 0 1px; color: #111; }
      .sr-cat { font-size: 11px; color: #aaa; margin-top: 1px; }
      .sr-desc { font-size: 12px; color: #666; margin-top: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
      .sr-empty { padding: 16px 14px; font-size: 13px; color: #aaa; text-align: center; }
      @media (max-width: 768px) {
        #search-input { width: 130px; }
        #search-input:focus { width: 170px; }
        #search-results { width: 280px; }
      }
    `;
    document.head.appendChild(style);

    const input = document.getElementById('search-input');
    const results = document.getElementById('search-results');
    let index = null;

    // Always use absolute URL so it works from any page depth
    fetch(SITE + '/assets/search-index.json')
      .then(r => r.json())
      .then(d => { index = d; });

    function esc(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }

    function highlight(text, q) {
      return text.replace(new RegExp(`(${esc(q)})`, 'gi'), '<mark>$1</mark>');
    }

    function doSearch(q) {
      if (!index || !q) { results.hidden = true; return; }
      const ql = q.toLowerCase();
      const hits = index.filter(e =>
        e.name.toLowerCase().includes(ql) ||
        e.cat.toLowerCase().includes(ql) ||
        e.desc.toLowerCase().includes(ql)
      ).slice(0, 12);

      if (!hits.length) {
        results.innerHTML = `<div class="sr-empty">No results for "${q}"</div>`;
      } else {
        results.innerHTML = hits.map(e => {
          const cat = e.subcat ? `${e.cat} / ${e.subcat}` : e.cat;
          return `<a class="sr" href="${SITE}${e.url}">
            <div class="sr-name">${highlight(e.name, q)}</div>
            <div class="sr-cat">${cat}</div>
            <div class="sr-desc">${e.desc}</div>
          </a>`;
        }).join('');
      }
      results.hidden = false;
    }

    input.addEventListener('input', e => doSearch(e.target.value.trim()));

    input.addEventListener('keydown', e => {
      if (e.key === 'Escape') { results.hidden = true; input.blur(); }
      if (e.key === 'Enter') {
        const first = results.querySelector('.sr');
        if (first) window.location.href = first.href;
      }
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        const first = results.querySelector('.sr');
        if (first) first.focus();
      }
    });

    results.addEventListener('keydown', e => {
      const items = [...results.querySelectorAll('.sr')];
      const idx = items.indexOf(document.activeElement);
      if (e.key === 'ArrowDown' && idx < items.length - 1) { e.preventDefault(); items[idx+1].focus(); }
      if (e.key === 'ArrowUp') { e.preventDefault(); idx > 0 ? items[idx-1].focus() : input.focus(); }
      if (e.key === 'Escape') { results.hidden = true; input.focus(); }
    });

    document.addEventListener('click', e => {
      if (!wrap.contains(e.target)) results.hidden = true;
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectSearch);
  } else {
    injectSearch();
  }
})();
