function setup() {
  createCanvas(640, 360);
}

function draw() {
  loadPixels();

  let n = (mouseX * 10.0) / width;

  let w = 16.0;
  let h = 16.0;

  let dx = w / width;
  let dy = h / height;

  let x = -w / 2.0;

  for (let i = 0; i < width; i++) {
    let y = -h / 2.0;

    for (let j = 0; j < height; j++) {
      let r = sqrt(x * x + y * y);
      let theta = atan2(y, x);

      let val = sin(n * cos(r) + 5.0 * theta);
      // let val = cos(r);
      // let val = sin(theta);

      let gray = (val + 1.0) * 255.0 / 2.0;

      let index = 4 * (i + j * width);

      pixels[index]     = gray;
      pixels[index + 1] = gray;
      pixels[index + 2] = gray;
      pixels[index + 3] = 255;

      y += dy;
    }

    x += dx;
  }

  updatePixels();
}
