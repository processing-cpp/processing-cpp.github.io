let diameter;
let angle = 0.0;

function setup() {
  createCanvas(640, 360);
  diameter = height - 10.0;
  noStroke();
  fill(255, 204, 0);
}

function draw() {
  background(0);

  let d1 = 10.0 + (sin(angle) * diameter / 2.0) + diameter / 2.0;
  let d2 = 10.0 + (sin(angle + PI / 2.0) * diameter / 2.0) + diameter / 2.0;
  let d3 = 10.0 + (sin(angle + PI) * diameter / 2.0) + diameter / 2.0;

  ellipse(0, height / 2, d1, d1);
  ellipse(width / 2, height / 2, d2, d2);
  ellipse(width, height / 2, d3, d3);

  angle += 0.02;
}
