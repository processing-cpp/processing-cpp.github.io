let bot;

function preload() {
  bot = loadImage("bot1.svg");
}

function setup() {
  createCanvas(640, 360);
}

function draw() {
  background(102);

  // Draw at coordinate (110, 90) at size 100 × 100
  image(bot, 110, 90, 100, 100);

  // Draw at coordinate (280, 40) at the SVG's natural size
  image(bot, 280, 40);
}
