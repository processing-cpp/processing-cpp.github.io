function setup() {
  noCanvas();

  fetch('https://processing-cpp.github.io/assets/data/usa-wikipedia.svg')
    .then(r => r.text())
    .then(svgText => {
      let parser = new DOMParser();
      let svgDoc = parser.parseFromString(svgText, 'image/svg+xml');
      let svgEl = svgDoc.documentElement;

      svgEl.setAttribute('width', '640');
      svgEl.setAttribute('height', '360');
      svgEl.setAttribute('viewBox', '600 180 1200 720');

      let mi = svgEl.querySelector('#MI, [id="MI"]');
      if (mi) { mi.style.fill = '#003366'; mi.style.stroke = 'none'; }

      let oh = svgEl.querySelector('#OH, [id="OH"]');
      if (oh) { oh.style.fill = '#990000'; oh.style.stroke = 'none'; }

      document.body.style.background = '#fff';
      document.body.style.margin = '0';
      document.body.appendChild(svgEl);
    });
}

function draw() {}
