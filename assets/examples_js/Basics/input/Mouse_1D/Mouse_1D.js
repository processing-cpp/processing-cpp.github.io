function setup() {
  createCanvas(640, 360);
  noStroke();
  colorMode(RGB, height, height, height);
  rectMode(CENTER);
}

function draw() {
  background(0);

  let r1 = map(mouseX, 0, width, 0, height);
  let r2 = height - r1;

  fill(r1);
  rect(width / 2 + r1 / 2, height / 2, r1, r1);

  fill(r2);
  rect(width / 2 - r2 / 2, height / 2, r2, r2);
}
