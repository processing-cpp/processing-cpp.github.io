function setup() {
  createCanvas(640, 360, WEBGL);
  noStroke();
}

function draw() {
  lights();
  background(0);

  let cameraY = height / 2;
  let fov = (mouseX / width) * PI / 2;
  let cameraZ = cameraY / tan(fov / 2);
  let aspect = width / height;

  if (mouseIsPressed) {
    aspect /= 2;
  }

  perspective(fov, aspect, cameraZ / 10, cameraZ * 10);

  translate(30, 0, 0);
  rotateX(-PI / 6);
  rotateY(PI / 3 + (mouseY / height) * PI);

  box(45);

  translate(0, 0, -50);
  box(30);
}