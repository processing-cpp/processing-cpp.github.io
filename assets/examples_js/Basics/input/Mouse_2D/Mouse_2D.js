function setup() {
  createCanvas(640, 360);
  noStroke();
  rectMode(CENTER);
}

function draw() {
  background(51);

  fill(255, 204);
  rect(mouseX, height / 2, mouseY / 2 + 10, mouseY / 2 + 10);

  let inverseX = width - mouseX;
  let inverseY = height - mouseY;

  rect(inverseX, height / 2, inverseY / 2 + 10, inverseY / 2 + 10);
}