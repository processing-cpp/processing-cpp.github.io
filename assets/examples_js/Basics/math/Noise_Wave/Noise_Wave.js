let yoff = 0.0;

function setup() {
  createCanvas(640, 360);
}

function draw() {
  background(51);
  fill(255);

  beginShape();

  let xoff = 0.0;

  for (let x = 0; x <= width; x += 10) {
    let n = noise(xoff, yoff);
    let y = map(n, 0, 1, 200, 300);

    vertex(x, y);

    xoff += 0.05;
  }

  yoff += 0.01;

  vertex(width, height);
  vertex(0, height);

  endShape(CLOSE);
}