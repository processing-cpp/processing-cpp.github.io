let maxHeight = 40;
let minHeight = 20;
let letterHeight = maxHeight;
let letterWidth = 20;

let x = -20;
let y = 0;

let newletter = false;

let numChars = 26;
let colors = [];

function setup() {
  createCanvas(640, 360);
  noStroke();
  colorMode(HSB, numChars);

  background(numChars / 2);

  for (let i = 0; i < numChars; i++) {
    colors[i] = color(i, numChars, numChars);
  }
}

function draw() {
  if (newletter) {
    let y_pos;

    if (letterHeight === maxHeight) {
      y_pos = y;
      fill(currentFill);
      rect(x, y_pos, letterWidth, letterHeight);
    } else {
      y_pos = y + minHeight;
      rect(x, y_pos, letterWidth, letterHeight);

      fill(numChars / 2);
      rect(x, y_pos - minHeight, letterWidth, letterHeight);
    }

    newletter = false;
  }
}

let currentFill;

function keyPressed() {
  if (
    (key >= 'A' && key <= 'Z') ||
    (key >= 'a' && key <= 'z')
  ) {
    let keyIndex;

    if (key <= 'Z') {
      keyIndex = key.charCodeAt(0) - 'A'.charCodeAt(0);
      letterHeight = maxHeight;
    } else {
      keyIndex = key.charCodeAt(0) - 'a'.charCodeAt(0);
      letterHeight = minHeight;
    }

    currentFill = colors[keyIndex];
  } else {
    currentFill = color(0);
    letterHeight = 10;
  }

  newletter = true;

  x += letterWidth;

  if (x > width - letterWidth) {
    x = 0;
    y += maxHeight;
  }

  if (y > height - letterHeight) {
    y = 0;
  }
}