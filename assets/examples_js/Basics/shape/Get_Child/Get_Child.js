// Fetch and manipulate SVG directly via DOM
let svgDoc;

function setup() {
  noLoop();
  let container = document.getElementById('p5-container') || document.body;
  container.style.background = '#fff';

  fetch('https://processing-cpp.github.io/assets/data/usa-wikipedia.svg')
    .then(r => r.text())
    .then(svgText => {
      let parser = new DOMParser();
      svgDoc = parser.parseFromString(svgText, 'image/svg+xml');
      let svgEl = svgDoc.documentElement;

      // Style the full map
      svgEl.setAttribute('width', '640');
      svgEl.setAttribute('height', '360');
      svgEl.style.transform = 'translate(-600px, -180px) scale(1)';

      // Highlight Michigan
      let mi = svgEl.querySelector('#MI');
      if (mi) {
        mi.style.fill = '#003366';
        mi.style.stroke = 'none';
      }

      // Highlight Ohio
      let oh = svgEl.querySelector('#OH');
      if (oh) {
        oh.style.fill = '#990000';
        oh.style.stroke = 'none';
      }

      container.innerHTML = '';
      container.appendChild(svgEl);
    });
}

function draw() {}
