function setup() {
  createCanvas(640, 360, WEBGL);
  noStroke();
}

function draw() {
  defineLights();
  background(0);

  for (let x = 0; x <= width; x += 60) {
    for (let y = 0; y <= height; y += 60) {
      push();

      translate(
        x - width / 2,
        y - height / 2,
        0
      );

      rotateY(map(mouseX, 0, width, 0, PI));
      rotateX(map(mouseY, 0, height, 0, PI));

      box(90);

      pop();
    }
  }
}

function defineLights() {
  pointLight(150, 100, 0, 200, -150, 0);

  directionalLight(0, 102, 255, 1, 0, 0);

  spotLight(
    255,
    255,
    109,
    0,
    40,
    200,
    0,
    -0.5,
    -0.5,
    PI / 2,
    2
  );
}