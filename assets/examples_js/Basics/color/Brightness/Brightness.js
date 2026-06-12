let barWidth = 20;
let lastBar = -1;

function setup() {
  createCanvas(640, 360);

  // HSB: hue ranges from 0 to width,
  // saturation from 0 to 100,
  // brightness from 0 to height
  colorMode(HSB, width, 100, height);

  noStroke();
  background(0);
}

function draw() {
  let whichBar = floor(mouseX / barWidth);

  if (whichBar !== lastBar) {
    let barX = whichBar * barWidth;

    fill(barX, 100, mouseY);
    rect(barX, 0, barWidth, height);

    lastBar = whichBar;
  }
}
