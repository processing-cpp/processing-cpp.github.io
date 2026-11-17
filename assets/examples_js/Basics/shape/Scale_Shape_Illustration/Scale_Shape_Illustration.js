let bot;

function preload() {
  bot = loadImage("bot1.svg");
}

function setup() {
  createCanvas(640, 360);
}

function draw() {
  background(102);

  push();

  translate(width / 2, height / 2);

  let zoom = map(mouseX, 0, width, 0.1, 4.5);

  scale(zoom);

  image(bot, -140, -140);

  pop();
}
