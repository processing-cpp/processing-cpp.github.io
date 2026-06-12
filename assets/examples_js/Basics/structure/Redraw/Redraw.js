let y;

function setup() {
  createCanvas(640, 360);
  stroke(255);
  noLoop();

  y = height * 0.5;
}

function draw() {
  background(0);

  y = y - 4;

  if (y < 0) {
    y = height;
  }

  line(0, y, width, y);
}

function mousePressed() {
  redraw();
}
