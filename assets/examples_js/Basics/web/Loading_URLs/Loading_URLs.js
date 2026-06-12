let overButton = false;

function setup() {
  createCanvas(640, 360);
}

function draw() {
  background(204);

  if (overButton) {
    fill(255);
  } else {
    noFill();
  }

  rect(105, 60, 75, 75);

  line(135, 105, 155, 85);
  line(140, 85, 155, 85);
  line(155, 85, 155, 100);
}

function mousePressed() {
  if (overButton) {
    window.open("http://www.processing.org", "_blank");
  }
}

function mouseMoved() {
  checkButtons();
}

function mouseDragged() {
  checkButtons();
}

function checkButtons() {
  if (
    mouseX > 105 &&
    mouseX < 180 &&
    mouseY > 60 &&
    mouseY < 135
  ) {
    overButton = true;
  } else {
    overButton = false;
  }
}
