let bx;
let by;
let boxSize = 75;
let overBox = false;
let locked = false;
let xOffset = 0.0;
let yOffset = 0.0;

function setup() {
  createCanvas(640, 360);
  bx = width / 2.0;
  by = height / 2.0;
  rectMode(RADIUS);
}

function draw() {
  background(0);

  if (
    mouseX > bx - boxSize &&
    mouseX < bx + boxSize &&
    mouseY > by - boxSize &&
    mouseY < by + boxSize
  ) {
    overBox = true;

    if (!locked) {
      stroke(255);
      fill(153);
    }
  } else {
    stroke(153);
    fill(153);
    overBox = false;
  }

  rect(bx, by, boxSize, boxSize);
}

function mousePressed() {
  if (overBox) {
    locked = true;
  } else {
    locked = false;
  }

  xOffset = mouseX - bx;
  yOffset = mouseY - by;
}

function mouseDragged() {
  if (locked) {
    bx = mouseX - xOffset;
    by = mouseY - yOffset;
  }
}

function mouseReleased() {
  locked = false;
}