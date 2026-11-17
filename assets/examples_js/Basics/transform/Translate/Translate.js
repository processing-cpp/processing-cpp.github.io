let x = 0;
let y;
let dim = 80;

function setup() {
  createCanvas(640, 360);
  noStroke();
}

function draw() {
  background(102);

  x = x + 0.8;

  if (x > width + dim) {
    x = -dim;
  }

  translate(x, height / 2 - dim / 2);

  fill(255);
  rect(-dim / 2, -dim / 2, dim, dim);

  // Transforms accumulate. Notice how this rect moves
  // twice as fast as the other, but it has the same
  // parameter for the x-axis value
  translate(x, dim);

  fill(0);
  rect(-dim / 2, -dim / 2, dim, dim);
}
