let xspacing = 8;
let w;
let maxwaves = 4;

let theta = 0.0;
let amplitude = [];
let dx = [];
let yvalues = [];

function setup() {
  createCanvas(640, 360);
  frameRate(30);

  colorMode(RGB, 255, 255, 255, 100);

  w = width + 16;

  for (let i = 0; i < maxwaves; i++) {
    amplitude[i] = random(10, 30);

    let period = random(100, 300);
    dx[i] = (TWO_PI / period) * xspacing;
  }

  yvalues = new Array(floor(w / xspacing));
}

function calcWave() {
  theta += 0.02;

  let len = floor(w / xspacing);

  for (let i = 0; i < len; i++) {
    yvalues[i] = 0;
  }

  for (let j = 0; j < maxwaves; j++) {
    let x = theta;

    for (let i = 0; i < len; i++) {
      if (j % 2 === 0) {
        yvalues[i] += sin(x) * amplitude[j];
      } else {
        yvalues[i] += cos(x) * amplitude[j];
      }

      x += dx[j];
    }
  }
}

function renderWave() {
  noStroke();
  fill(255, 50);

  ellipseMode(CENTER);

  let len = floor(w / xspacing);

  for (let x = 0; x < len; x++) {
    ellipse(
      x * xspacing,
      height / 2 + yvalues[x],
      16,
      16
    );
  }
}

function draw() {
  background(0);

  calcWave();
  renderWave();
}
