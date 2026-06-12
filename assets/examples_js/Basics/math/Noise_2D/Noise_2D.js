let increment = 0.02;

function setup() {
  createCanvas(640, 360);
}

function draw() {
  loadPixels();

  let xoff = 0.0;

  let detail = map(mouseX, 0, width, 0.1, 0.6);
  noiseDetail(8, detail);

  for (let x = 0; x < width; x++) {
    xoff += increment;
    let yoff = 0.0;

    for (let y = 0; y < height; y++) {
      yoff += increment;

      let bright = noise(xoff, yoff) * 255;

      let index = (x + y * width) * 4;

      pixels[index] = bright;
      pixels[index + 1] = bright;
      pixels[index + 2] = bright;
      pixels[index + 3] = 255;
    }
  }

  updatePixels();
}