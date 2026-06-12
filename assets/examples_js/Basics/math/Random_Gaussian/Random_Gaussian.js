function setup() {
  createCanvas(640, 360);
  background(0);
}

function draw() {
  let val = randomGaussian();

  let sd = 60.0;
  let mean = width / 2.0;
  let x = (val * sd) + mean;

  noStroke();
  fill(255, 10);
  ellipse(x, height / 2.0, 32, 32);
}