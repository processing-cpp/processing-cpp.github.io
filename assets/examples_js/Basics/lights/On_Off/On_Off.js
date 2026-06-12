let spin = 0.0;

function setup() {
  createCanvas(640, 360, WEBGL);
  noStroke();
}

function draw() {
  background(51);

  if (!mouseIsPressed) {
    lights();
  }

  spin += 0.01;

  push();
  rotateX(PI / 9.0);
  rotateY(PI / 5.0 + spin);
  box(150);
  pop();
}