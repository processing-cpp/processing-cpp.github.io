let increment = 0.01;
let zoff = 0.0;
let zincrement = 0.02;

function setup() {
  createCanvas(640, 360);
  frameRate(30);
}

function draw() {
  loadPixels();

  let xoff = 0.0;

  for (let x = 0; x < width; x++) {
    xoff += increment;
    let yoff = 0.0;

    for (let y = 0; y < height; y++) {
      yoff += increment;

      let bright = noise(xoff, yoff, zoff) * 255;

      let idx = (x + y * width) * 4;
      pixels[idx] = bright;
      pixels[idx + 1] = bright;
      pixels[idx + 2] = bright;
      pixels[idx + 3] = 255;
    }
  }

  updatePixels();
  zoff += zincrement;
}