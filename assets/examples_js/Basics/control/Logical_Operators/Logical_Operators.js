function setup() {
  createCanvas(640, 360);
  background(126);

  let test = false;

  for (let i = 5; i <= height; i += 5) {
    stroke(0);
    if ((i > 35) && (i < 100)) {
      line(width / 4, i, width / 2, i);
      test = false;
    }

    stroke(76);
    if ((i <= 35) || (i >= 100)) {
      line(width / 2, i, width, i);
      test = true;
    }

    if (test) {
      stroke(0);
      point(width / 3, i);
    }

    if (!test) {
      stroke(255);
      point(width / 4, i);
    }
  }

  noLoop();
}