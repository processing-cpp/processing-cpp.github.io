function setup() {
  createCanvas(640, 360, WEBGL);
  noStroke();
}

function draw() {
  background(0);
  lights();
  let cameraY = height / 2.0;
  let fov = mouseX / width * PI / 2;
  let cameraZ = cameraY / tan(fov / 2.0);
  let aspect = width / height;
  if (mouseIsPressed) {
    aspect = aspect / 2.0;
  }
  perspective(fov, aspect, cameraZ / 10.0, cameraZ * 10.0);
  translate(30, 0, 0);
  rotateX(-PI / 6);
  rotateY(PI / 3 + mouseY / height * PI);
  box(45);
  translate(0, 0, -50);
  box(30);
}
