let angle = 0;
let jitter = 0;

function setup() {
  createCanvas(640, 360);

  noStroke();
  fill(255);

  rectMode(CENTER);
}

function draw() {
  background(51);

  // during even-numbered seconds (0, 2, 4, 6...)
  if (second() % 2 === 0) {
    jitter = random(-0.1, 0.1);
  }

  angle = angle + jitter;

  let c = cos(angle);

  translate(width / 2, height / 2);
  rotate(c);

  rect(0, 0, 180, 180);
}
