let y = 180;

function setup() {
  createCanvas(640, 360);
  stroke(255);
  noLoop();
}

function draw() {
  background(0);

  line(0, y, width, y);

  y = y - 1;

  if (y < 0) {
    y = height;
  }
}
