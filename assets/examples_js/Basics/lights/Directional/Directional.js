function setup() {
  createCanvas(640, 360, WEBGL);
  noStroke();
  fill(204);
}

function draw() {
  background(0);

  let dirY = (mouseY / height - 0.5) * 2;
  let dirX = (mouseX / width - 0.5) * 2;

  directionalLight(204, 204, 204, -dirX, -dirY, -1);

  push();
  translate(-100, 0, 0);
  sphere(80);
  pop();

  push();
  translate(100, 0, 0);
  sphere(80);
  pop();
}