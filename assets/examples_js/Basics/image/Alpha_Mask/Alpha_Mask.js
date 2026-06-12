let img;
let imgMask;

function setup() {
  createCanvas(640, 360);

  img = loadImage("moonwalk.jpg");
  imgMask = loadImage("mask.jpg");

  imageMode(CENTER);
}

function draw() {
  background(0, 102, 153);

  if (img && imgMask) {
    img.mask(imgMask);

    image(img, width / 2, height / 2);
    image(img, mouseX, mouseY);
  }
}