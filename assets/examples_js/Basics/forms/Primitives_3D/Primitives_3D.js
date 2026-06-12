function setup() {
  createCanvas(640, 360, WEBGL);
}

function draw() {
  background(0);
  lights();

  noStroke();

  push();
  translate(-width / 2 + 130, 0, 0);
  rotateY(1.25);
  rotateX(-0.4);
  box(100);
  pop();

  noFill();
  stroke(255);

  push();
  translate(-width / 2 + 500, height * 0.35 - height / 2, -200);
  sphere(280);
  pop();
}