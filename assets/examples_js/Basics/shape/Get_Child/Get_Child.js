function setup() {
  noCanvas();
  fetch('https://processing-cpp.github.io/assets/data/usa-wikipedia.svg')
    .then(r => r.text())
    .then(svgText => {
      let parser = new DOMParser();
      let svgDoc = parser.parseFromString(svgText, 'image/svg+xml');
      let svgEl = svgDoc.documentElement;

      // Get original viewBox to center properly
      let vb = svgEl.getAttribute('viewBox') || '0 0 960 600';
      svgEl.setAttribute('width', '640');
      svgEl.setAttribute('height', '360');
      svgEl.setAttribute('viewBox', vb);
      svgEl.setAttribute('preserveAspectRatio', 'xMidYMid meet');

      let mi = svgEl.querySelector('#MI');
      if (mi) { mi.style.fill = '#003366'; mi.style.stroke = '#fff'; mi.style.strokeWidth = '1px'; }

      let oh = svgEl.querySelector('#OH');
      if (oh) { oh.style.fill = '#990000'; oh.style.stroke = '#fff'; oh.style.strokeWidth = '1px'; }

      document.body.style.background = '#fff';
      document.body.style.margin = '0';
      document.body.style.overflow = 'hidden';
      document.body.appendChild(svgEl);
    });
}

function draw() {}
