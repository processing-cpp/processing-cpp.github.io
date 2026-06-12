let img;
let offset = 0;
let easing = 0.05;

function setup() {
  createCanvas(640, 360);
  img = loadImage("moonwalk.jpg");
}

function draw() {
  image(img, 0, 0);

  let dx = (mouseX - img.width / 2) - offset;
  offset += dx * easing;

  tint(255, 127);
  image(img, offset, 0);
  noTint();
}