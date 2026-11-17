function setup() {
  createCanvas(640, 360);
  noStroke();

  const inside = color(204, 102, 0);
  const middle = color(204, 153, 0);
  const outside = color(153, 51, 0);

  background(51, 0, 0);

  push();
  translate(80, 80);
  fill(outside);
  rect(0, 0, 200, 200);
  fill(middle);
  rect(40, 60, 120, 120);
  fill(inside);
  rect(60, 90, 80, 80);
  pop();

  push();
  translate(360, 80);
  fill(inside);
  rect(0, 0, 200, 200);
  fill(outside);
  rect(40, 60, 120, 120);
  fill(middle);
  rect(60, 90, 80, 80);
  pop();

  noLoop();
}