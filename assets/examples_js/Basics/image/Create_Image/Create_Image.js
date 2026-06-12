let img;

function setup() {
  createCanvas(640, 360);

  img = createImage(230, 230);

  img.loadPixels();

  let total = img.width * img.height;

  for (let i = 0; i < total; i++) {
    let a = map(i, 0, total, 255, 0);

    let index = i * 4;

    img.pixels[index] = 0;
    img.pixels[index + 1] = 153;
    img.pixels[index + 2] = 204;
    img.pixels[index + 3] = a;
  }

  img.updatePixels();
}

function draw() {
  background(0);

  image(img, 90, 80);

  image(
    img,
    mouseX - img.width / 2,
    mouseY - img.height / 2
  );
}