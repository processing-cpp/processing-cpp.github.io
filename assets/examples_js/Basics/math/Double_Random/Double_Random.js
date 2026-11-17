let totalPts = 300;
let steps = totalPts + 1;

function setup() {
  createCanvas(640, 360);
  stroke(255);
  frameRate(1);
}

function draw() {
  background(0);

  let randVal = 0.0;

  for (let i = 1; i < steps; i++) {
    point(
      (width / steps) * i,
      (height / 2.0) + random(-randVal, randVal)
    );

    randVal += random(-5.0, 5.0);
  }
}
