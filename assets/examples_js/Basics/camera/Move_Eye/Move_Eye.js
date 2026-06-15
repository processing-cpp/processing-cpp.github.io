function setup() {
  createCanvas(640, 360, WEBGL);
  fill(204);
}

function draw() {
  background(0);
  lights();

  // Map mouseY so moving mouse up lifts camera
  let eyeY = map(mouseY, 0, height, -200, 200);

  camera(30, eyeY, 500,   // eye — pushed back so box is fully visible
         0, 0, 0,          // center
         0, 1, 0);         // up

  noStroke();
  box(90);
  stroke(255);
  line(-100, 0, 0, 100, 0, 0);
  line(0, -100, 0, 0, 100, 0);
  line(0, 0, -100, 0, 0, 100);
}
