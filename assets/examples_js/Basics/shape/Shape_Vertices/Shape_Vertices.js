let points = [];
let frameC = 0;

function setup() {
  createCanvas(640, 360);
  fetch('https://processing-cpp.github.io/assets/data/uk.svg')
    .then(r => r.text())
    .then(svgText => {
      let parser = new DOMParser();
      let doc = parser.parseFromString(svgText, 'image/svg+xml');
      let paths = doc.querySelectorAll('path, polygon, polyline');
      let allPts = [];
      let childIdx = 0;
      paths.forEach(path => {
        let pts = [];
        if (path.tagName === 'polygon' || path.tagName === 'polyline') {
          let coords = path.getAttribute('points').trim().split(/[\s,]+/);
          for (let i = 0; i < coords.length - 1; i += 2) {
            pts.push({ x: parseFloat(coords[i]), y: parseFloat(coords[i+1]), child: childIdx });
          }
        } else {
          let len = path.getTotalLength();
          let step = max(1, len / 100);
          for (let t = 0; t < len; t += step) {
            let pt = path.getPointAtLength(t);
            pts.push({ x: pt.x, y: pt.y, child: childIdx });
          }
        }
        allPts = allPts.concat(pts);
        childIdx++;
      });

      // Get bounding box
      let svgEl = doc.documentElement;
      let vb = svgEl.getAttribute('viewBox');
      let svgW = vb ? parseFloat(vb.split(' ')[2]) : parseFloat(svgEl.getAttribute('width') || 640);
      let svgH = vb ? parseFloat(vb.split(' ')[3]) : parseFloat(svgEl.getAttribute('height') || 360);

      // Scale to center in canvas
      let scale = min(width / svgW, height / svgH) * 0.9;
      let offX = (width - svgW * scale) / 2;
      let offY = (height - svgH * scale) / 2;

      points = allPts.map((p, j) => ({
        x: p.x * scale + offX,
        y: p.y * scale + offY,
        child: p.child,
        j: j
      }));
    });
}

function draw() {
  background(51);
  for (let p of points) {
    stroke((frameC + (p.child + 1) * p.j) % 255);
    point(p.x, p.y);
  }
  frameC++;
}
