let showPerspective = false;

function setup() {
  createCanvas(600, 360, WEBGL);
  noStroke();
  fill(255);
}

function draw() {
  background(0);
  lights();
  let far = map(mouseX, 0, width, 500, 2000);
  if (showPerspective) {
    perspective(PI / 3.0, width / height, 1, far);
  } else {
    ortho(-width / 2.0, width / 2.0, -height / 2.0, height / 2.0, 1, far);
  }
  rotateX(-PI / 6);
  rotateY(PI / 3);
  box(180);
}

function mousePressed() {
  showPerspective = !showPerspective;
}
