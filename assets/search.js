(function() {
  const BASE = 'https://processing-cpp.github.io';

  // Inject search bar into nav after nav.js runs
  function injectSearch() {
    const nav = document.getElementById('site-nav');
    if (!nav) return;

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
      #search-box { position: relative; }
      #search-input {
        width: 220px;
        padding: 6px 12px;
        border: 1px solid #e0e0e0;
        border-radius: 20px;
        font-size: 13px;
        font-family: inherit;
        background: #f8f8f8;
        outline: none;
        transition: border-color 0.15s, width 0.2s;
      }
      #search-input:focus {
        border-color: #aaa;
        background: #fff;
        width: 280px;
      }
      #search-results {
        position: absolute;
        top: calc(100% + 8px);
        right: 0;
        width: 360px;
        background: #fff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.1);
        max-height: 400px;
        overflow-y: auto;
        z-index: 1000;
      }
      .search-result {
        display: block;
        padding: 10px 14px;
        border-bottom: 1px solid #f0f0f0;
        text-decoration: none;
        color: #111;
        transition: background 0.1s;
      }
      .search-result:last-child { border-bottom: none; }
      .search-result:hover { background: #f8f8f8; }
      .search-result-name {
        font-family: "SF Mono","Fira Code",monospace;
        font-size: 13px;
        font-weight: 600;
        color: #111;
      }
      .search-result-name mark {
        background: #fff3b0;
        color: #111;
        border-radius: 2px;
        padding: 0 1px;
      }
      .search-result-cat {
        font-size: 11px;
        color: #aaa;
        margin-top: 1px;
      }
      .search-result-desc {
        font-size: 12px;
        color: #666;
        margin-top: 3px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .search-no-results {
        padding: 16px 14px;
        font-size: 13px;
        color: #aaa;
        text-align: center;
      }
      @media (max-width: 768px) {
        #search-wrap { padding-right: 0.5rem; }
        #search-input { width: 140px; }
        #search-input:focus { width: 180px; }
        #search-results { width: 280px; right: 0; }
      }
    `;
    document.head.appendChild(style);

    const input = document.getElementById('search-input');
    const results = document.getElementById('search-results');
    let index = null;

    // Load index
    fetch(BASE + '/assets/search-index.json')
      .then(r => r.json())
      .then(data => { index = data; });

    function highlight(text, query) {
      const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      return text.replace(new RegExp(`(${escaped})`, 'gi'), '<mark>$1</mark>');
    }

    function search(q) {
      if (!index || q.length < 1) { results.hidden = true; return; }
      const ql = q.toLowerCase();
      const matches = index.filter(e =>
        e.name.toLowerCase().includes(ql) ||
        e.cat.toLowerCase().includes(ql) ||
        e.desc.toLowerCase().includes(ql)
      ).slice(0, 12);

      if (!matches.length) {
        results.innerHTML = `<div class="search-no-results">No results for "${q}"</div>`;
        results.hidden = false;
        return;
      }

      results.innerHTML = matches.map(e => {
        const cat = e.subcat ? `${e.cat} / ${e.subcat}` : e.cat;
        return `<a class="search-result" href="${BASE}${e.url}">
          <div class="search-result-name">${highlight(e.name, q)}</div>
          <div class="search-result-cat">${cat}</div>
          <div class="search-result-desc">${e.desc}</div>
        </a>`;
      }).join('');
      results.hidden = false;
    }

    input.addEventListener('input', e => search(e.target.value.trim()));

    input.addEventListener('keydown', e => {
      if (e.key === 'Escape') { results.hidden = true; input.blur(); }
      if (e.key === 'Enter') {
        const first = results.querySelector('.search-result');
        if (first) window.location.href = first.href;
      }
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        const items = [...results.querySelectorAll('.search-result')];
        if (items.length) items[0].focus();
      }
    });

    results.addEventListener('keydown', e => {
      const items = [...results.querySelectorAll('.search-result')];
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
