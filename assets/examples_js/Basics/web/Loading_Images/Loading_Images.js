let img;

function preload() {
  img = loadImage('https://processing-cpp.github.io/assets/data/processing-web.png');
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
