let x = 0;
let y = 0;
let easing = 0.05;

function setup() {
  createCanvas(640, 360);
  noStroke();
}

function draw() {
  background(51);

  let targetX = mouseX;
  let dx = targetX - x;
  x += dx * easing;

  let targetY = mouseY;
  let dy = targetY - y;
  y += dy * easing;

  ellipse(x, y, 66, 66);
}