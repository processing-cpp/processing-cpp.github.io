let x = 0.0;
let y = 0.0;

function setup() {
  createCanvas(640, 360);
  noStroke();
}

function draw() {
  background(51);

  x = lerp(x, mouseX, 0.05);
  y = lerp(y, mouseY, 0.05);

  fill(255);
  stroke(255);
  ellipse(x, y, 66, 66);
}
