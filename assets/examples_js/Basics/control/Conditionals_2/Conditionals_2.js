function setup() {
  createCanvas(640, 360);
  background(0);

  for (let i = 2; i < width - 2; i += 2) {
    if ((i % 20) === 0) {
      stroke(255);
      line(i, 80, i, height / 2);
    } else if ((i % 10) === 0) {
      stroke(153);
      line(i, 20, i, 180);
    } else {
      stroke(102);
      line(i, height / 2, i, height - 20);
    }
  }

  noLoop();
}