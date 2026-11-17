(function () {
  function highlight() {
    // Handle <pre> blocks
    document.querySelectorAll('pre').forEach(function (pre) {
      if (pre.dataset.cmDone) return;
      pre.dataset.cmDone = '1';
      var code = pre.querySelector('code');
      var text = (code ? code.textContent : pre.textContent).replace(/^\n/, '');
      var wrapper = document.createElement('div');
      wrapper.className = 'cm-static-wrap';
      pre.parentNode.insertBefore(wrapper, pre);
      pre.style.display = 'none';
      CodeMirror(wrapper, {
        value: text,
        mode: 'cppmode',
        theme: 'cppmode',
        readOnly: true,
        lineNumbers: false,
        lineWrapping: false,
        scrollbarStyle: 'null',
        viewportMargin: Infinity,
      });
    });

    // Handle .syntax-block divs (reference pages)
    document.querySelectorAll('.syntax-block').forEach(function (el) {
      if (el.dataset.cmDone) return;
      el.dataset.cmDone = '1';
      var text = el.textContent.replace(/^\n/, '');
      var wrapper = document.createElement('div');
      wrapper.className = 'cm-static-wrap cm-syntax-wrap';
      el.parentNode.insertBefore(wrapper, el);
      el.style.display = 'none';
      CodeMirror(wrapper, {
        value: text,
        mode: 'cppmode',
        theme: 'cppmode',
        readOnly: true,
        lineNumbers: false,
        lineWrapping: false,
        scrollbarStyle: 'null',
        viewportMargin: Infinity,
      });
    });

    // Handle .impl-block divs (reference pages - dark background)
    document.querySelectorAll('.impl-block').forEach(function (el) {
      if (el.dataset.cmDone) return;
      el.dataset.cmDone = '1';
      var text = el.textContent.replace(/^\n/, '');
      var wrapper = document.createElement('div');
      wrapper.className = 'cm-static-wrap cm-impl-wrap';
      el.parentNode.insertBefore(wrapper, el);
      el.style.display = 'none';
      CodeMirror(wrapper, {
        value: text,
        mode: 'cppmode',
        theme: 'cppmode',
        readOnly: true,
        lineNumbers: true,
        lineWrapping: false,
        scrollbarStyle: 'native',
        viewportMargin: Infinity,
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', highlight);
  } else {
    highlight();
  }
})();
