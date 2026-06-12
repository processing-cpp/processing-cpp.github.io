let barWidth = 20;
let lastBar = -1;

function setup() {
  createCanvas(640, 360);
  colorMode(HSB, width, height, 100);
  noStroke();
}

function draw() {
  let whichBar = floor(mouseX / barWidth);

  if (whichBar !== lastBar) {
    let barX = whichBar * barWidth;

    fill(barX, mouseY, 66);

    rect(barX, 0, barWidth, height);
    lastBar = whichBar;
  }
}