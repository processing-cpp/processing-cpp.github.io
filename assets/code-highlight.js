/* code-highlight.js
   Converts static code blocks to read-only CodeMirror instances.
   Handles: <pre><code>, <pre>, .syntax-block, .impl-block
   Loaded at end of <body> so DOM is already available -- no DOMContentLoaded needed. */

(function () {
  function highlight() {
    // <pre> and <pre><code> blocks
    document.querySelectorAll('pre').forEach(function (pre) {
      if (pre.dataset.cmDone) return;
      pre.dataset.cmDone = '1';
      var code = pre.querySelector('code');
      var text = code ? code.textContent : pre.textContent;
      var wrapper = document.createElement('div');
      wrapper.className = 'cm-static-wrap';
      wrapper.style.cssText = 'margin-bottom:1.25rem;border-radius:8px;overflow:hidden;';
      pre.parentNode.insertBefore(wrapper, pre);
      pre.style.display = 'none';
      var cm = CodeMirror(wrapper, {
        value: text.replace(/^\n/, ''),
        mode: 'cppmode',
        theme: 'cppmode',
        readOnly: true,
        lineNumbers: false,
        lineWrapping: false,
        scrollbarStyle: 'null',
        viewportMargin: Infinity,
      });
      cm.getWrapperElement().style.fontSize = '13px';
    });

    // .syntax-block divs (reference pages - function signatures)
    document.querySelectorAll('.syntax-block').forEach(function (el) {
      if (el.dataset.cmDone) return;
      el.dataset.cmDone = '1';
      var text = el.textContent;
      var wrapper = document.createElement('div');
      wrapper.className = 'cm-static-wrap cm-syntax-wrap';
      wrapper.style.cssText = 'margin-bottom:0.5rem;border-radius:6px;overflow:hidden;background:#f8f8f8;';
      el.parentNode.insertBefore(wrapper, el);
      el.style.display = 'none';
      var cm = CodeMirror(wrapper, {
        value: text.replace(/^\n/, '').trim(),
        mode: 'cppmode',
        theme: 'cppmode',
        readOnly: true,
        lineNumbers: false,
        lineWrapping: false,
        scrollbarStyle: 'null',
        viewportMargin: Infinity,
      });
      cm.getWrapperElement().style.fontSize = '13px';
    });

    // .impl-block divs (reference pages - implementation examples)
    document.querySelectorAll('.impl-block').forEach(function (el) {
      if (el.dataset.cmDone) return;
      el.dataset.cmDone = '1';
      var text = el.textContent;
      var wrapper = document.createElement('div');
      wrapper.className = 'cm-static-wrap cm-impl-wrap';
      wrapper.style.cssText = 'margin-bottom:1.25rem;border-radius:6px;overflow:hidden;max-height:400px;';
      el.parentNode.insertBefore(wrapper, el);
      el.style.display = 'none';
      var cm = CodeMirror(wrapper, {
        value: text.replace(/^\n/, ''),
        mode: 'cppmode',
        theme: 'cppmode',
        readOnly: true,
        lineNumbers: true,
        lineWrapping: false,
        scrollbarStyle: 'native',
        viewportMargin: Infinity,
      });
      cm.getWrapperElement().style.fontSize = '12px';
    });
  }

  // Scripts load at end of body so DOM is ready -- call immediately
  // but also handle the rare case where this loads early
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', highlight);
  } else {
    highlight();
  }
})();
