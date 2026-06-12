let barWidth = 20;
let lastBar = -1;

function setup() {
  createCanvas(640, 360);
  colorMode(HSB, height, height, height);
  noStroke();
  background(0);
}

function draw() {
  let whichBar = floor(mouseX / barWidth);

  if (whichBar !== lastBar) {
    let barX = whichBar * barWidth;

    fill(mouseY, height, height);
    rect(barX, 0, barWidth, height);

    lastBar = whichBar;
  }
}