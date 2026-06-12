let bot;

function preload() {
  bot = loadImage("bot1.svg");
}

function setup() {
  createCanvas(640, 360);
  noLoop();
}

function draw() {
  background(102);
  // Left bot
  push();
  tint(0, 102, 153);
  image(bot, 20, 25, 300, 300);
  pop();
  // Right bot
  image(bot, 320, 25, 300, 300);
}
