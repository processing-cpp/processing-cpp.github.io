function setup() {
  createCanvas(640, 360);
  background(51);
  noFill();
  stroke(51);

  stroke(204);
  for (let i = 0; i < width - 20; i += 4) {
    if (i > (30 + 70)) {
      line(i, 0, i, 50);
    }
  }

  stroke(255);
  rect(4 + (2 * 8), 52, 290, 48);
  rect((4 + 2) * 8, 100, 290, 49);

  stroke(153);
  for (let i = 0; i < width; i += 2) {
    if (((i > 20) && (i < 50)) || ((i > 100) && (i < width - 20))) {
      line(i, 151, i, height - 1);
    }
  }
}