function setup() {
  noCanvas();
  fetch('https://processing-cpp.github.io/assets/data/usa-wikipedia.svg')
    .then(r => r.text())
    .then(svgText => {
      let parser = new DOMParser();
      let svgDoc = parser.parseFromString(svgText, 'image/svg+xml');
      let svgEl = svgDoc.documentElement;

      svgEl.setAttribute('width', '1368');
      svgEl.setAttribute('height', '936');
      svgEl.style.position = 'absolute';
      svgEl.style.left = '-600px';
      svgEl.style.top = '-180px';

      let mi = svgEl.querySelector('#MI');
      if (mi) { mi.style.fill = '#003366'; mi.style.stroke = '#fff'; mi.style.strokeWidth = '1px'; }

      let oh = svgEl.querySelector('#OH');
      if (oh) { oh.style.fill = '#990000'; oh.style.stroke = '#fff'; oh.style.strokeWidth = '1px'; }

      document.body.style.background = '#fff';
      document.body.style.margin = '0';
      document.body.style.overflow = 'hidden';
      document.body.style.position = 'relative';
      document.body.appendChild(svgEl);
    });
}

function draw() {}
