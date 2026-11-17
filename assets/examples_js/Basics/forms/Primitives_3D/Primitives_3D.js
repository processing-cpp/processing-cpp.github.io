function setup() {
  createCanvas(640, 360, WEBGL);
  noLoop();
}

function draw() {
  background(0);
  lights();
  noStroke();
  push();
  translate(-180, 0, 0);
  rotateY(1.25);
  rotateX(-0.4);
  box(100);
  pop();
  noFill();
  stroke(255);
  push();
  translate(170, -height * 0.15, -200);
  sphere(280);
  pop();
}
