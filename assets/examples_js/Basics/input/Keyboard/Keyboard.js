let rectWidth;

function setup() {
  createCanvas(640, 360);
  noStroke();
  background(0);

  rectWidth = width / 4;
}

function draw() {
  // intentionally empty (keeps loop running)
}

function keyPressed() {
  let keyIndex = -1;

  if (key >= 'A' && key <= 'Z') {
    keyIndex = key.charCodeAt(0) - 'A'.charCodeAt(0);
  } else if (key >= 'a' && key <= 'z') {
    keyIndex = key.charCodeAt(0) - 'a'.charCodeAt(0);
  }

  if (keyIndex === -1) {
    background(0);
  } else {
    fill(millis() % 255);

    let x = map(keyIndex, 0, 25, 0, width - rectWidth);
    rect(x, 0, rectWidth, height);
  }
}