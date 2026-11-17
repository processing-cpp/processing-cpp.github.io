function setup() {
  createCanvas(640, 360, WEBGL);
  noStroke();
  fill(204);
  sphereDetail(60);
}

function draw() {
  background(0);

  directionalLight(51, 102, 126, 0, -1, 0);

  spotLight(204, 153, 0, 360, 160, 600, 0, 0, -1, PI / 2, 600);

  spotLight(
    102,
    153,
    204,
    360,
    mouseY - height / 2,
    600,
    0,
    0,
    -1,
    PI / 2,
    600
  );

  sphere(120);
}