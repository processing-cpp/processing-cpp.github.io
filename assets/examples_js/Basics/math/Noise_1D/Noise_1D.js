let xoff = 0.0;
let xincrement = 0.01;

function setup() {
  createCanvas(640, 360);
  background(0);
  noStroke();
}

function draw() {
  fill(0, 10);
  rect(0, 0, width, height);

  // let n = random(width);

  let n = noise(xoff) * width;

  xoff += xincrement;

  fill(200);
  ellipse(n, height / 2, 64, 64);
}
