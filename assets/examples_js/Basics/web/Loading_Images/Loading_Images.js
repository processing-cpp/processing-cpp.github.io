let img;

function preload() {
  img = loadImage('processing-web.png');
}

function setup() {
  createCanvas(640, 360);
  noLoop();
}

function draw() {
  background(0);
  for (let i = 0; i < 5; i++) {
    image(img, 0, img.height * i);
  }
}
