function setup() {
  createCanvas(640, 360);
  background(0);
  stroke(255);

  let b = false;

  let d = 20;
  let middle = width / 2;

  for (let i = d; i <= width; i += d) {
    if (i < middle) {
      b = true;
    } else {
      b = false;
    }

    if (b === true) {
      line(i, d, i, height - d);
    }

    if (b === false) {
      line(middle, i - middle + d, width - d, i - middle + d);
    }
  }

  noLoop();
}