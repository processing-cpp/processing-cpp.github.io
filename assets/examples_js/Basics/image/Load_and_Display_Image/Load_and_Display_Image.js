let img;

function setup() {
  createCanvas(640, 360);

  img = loadImage("moonwalk.jpg");
}

function draw() {
  background(0);

  image(img, 0, 0);

  image(
    img,
    0,
    height / 2,
    img.width / 2,
    img.height / 2
  );
}