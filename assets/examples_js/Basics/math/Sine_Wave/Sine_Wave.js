let xspacing = 16;
let w;

let theta = 0.0;
let amplitude = 75.0;
let period = 500.0;
let dx;
let yvalues = [];

function setup() {
  createCanvas(640, 360);

  w = width + 16;
  dx = (TWO_PI / period) * xspacing;

  yvalues = new Array(Math.floor(w / xspacing));
}

function draw() {
  background(0);

  calcWave();
  renderWave();
}

function calcWave() {
  theta += 0.02;

  let x = theta;

  for (let i = 0; i < yvalues.length; i++) {
    yvalues[i] = sin(x) * amplitude;
    x += dx;
  }
}

function renderWave() {
  noStroke();
  fill(255);

  for (let i = 0; i < yvalues.length; i++) {
    ellipse(i * xspacing, height / 2 + yvalues[i], 16, 16);
  }
}
