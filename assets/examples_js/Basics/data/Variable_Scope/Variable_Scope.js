let a = 80;

function setup() {
  createCanvas(640, 360);
  background(0);
  stroke(255);
  noLoop();
}

function draw() {
  line(a, 0, a, height);
  for (let i = 120; i < 200; i += 2) {
    line(i, 0, i, height);
  }
  let b = 300;
  line(b, 0, b, height);
  drawAnotherLine();
  drawYetAnotherLine();
}

function drawAnotherLine() {
  let c = 320;
  line(c, 0, c, height);
}

function drawYetAnotherLine() {
  line(a + 2, 0, a + 2, height);
}
