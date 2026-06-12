let img;

function setup() {
  createCanvas(640, 360);

  img = loadImage("https://processing.org/img/processing-web.png");

  noLoop();
}

function draw() {
  background(0);

  if (img) {
    for (let i = 0; i < 5; i++) {
      image(img, 0, img.height * i);
    }
  }
}
