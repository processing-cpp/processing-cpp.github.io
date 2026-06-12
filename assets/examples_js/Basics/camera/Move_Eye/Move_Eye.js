function setup() {
  createCanvas(640, 360, WEBGL);
  fill(204);
}

function draw() {
  lights();
  background(0);

  camera(
    30.0, mouseY - height / 2, 220.0,
    0.0, 0.0, 0.0,
    0.0, 1.0, 0.0
  );

  noStroke();
  box(90);

  stroke(255);
  line(-100, 0, 0, 100, 0, 0);
  line(0, -100, 0, 0, 100, 0);
  line(0, 0, -100, 0, 0, 100);
}