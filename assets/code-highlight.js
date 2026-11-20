(function () {
  // Code blocks are as tall as their code, and as wide: a long line stays
  // one line, and the block scrolls sideways (shift + wheel, or the bar)
  if (!document.getElementById('cm-fit-style')) {
    var st = document.createElement('style');
    st.id = 'cm-fit-style';
    st.textContent =
      'html body .cm-static-wrap .CodeMirror { height: auto; }' +
      'html body .cm-static-wrap .CodeMirror-scroll { height: auto; max-height: none; overflow-x: auto !important; overflow-y: hidden !important; }' +
      'html body .cm-static-wrap .CodeMirror-hscrollbar { display: block !important; }';
    document.head.appendChild(st);
  }
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
      var cm = CodeMirror(wrapper, {
        value: text,
        mode: 'cppmode',
        theme: 'cppmode',
        readOnly: true,
        lineNumbers: false,
        lineWrapping: false,
        scrollbarStyle: 'native',
        viewportMargin: Infinity,
      });
      cm.setSize(null, 'auto');
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
      var cm = CodeMirror(wrapper, {
        value: text,
        mode: 'cppmode',
        theme: 'cppmode',
        readOnly: true,
        lineNumbers: false,
        lineWrapping: false,
        scrollbarStyle: 'native',
        viewportMargin: Infinity,
      });
      cm.setSize(null, 'auto');
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
      var cm = CodeMirror(wrapper, {
        value: text,
        mode: 'cppmode',
        theme: 'cppmode',
        readOnly: true,
        lineNumbers: true,
        lineWrapping: false,
        scrollbarStyle: 'native',
        viewportMargin: Infinity,
      });
      cm.setSize(null, 'auto');
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', highlight);
  } else {
    highlight();
  }
})();
