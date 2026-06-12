let showPerspective = false;

function setup() {
  createCanvas(600, 360, WEBGL);
  noStroke();
}

function draw() {
  background(0);
  lights();

  let far = map(mouseX, 0, width, 300, 1000);

  if (showPerspective) {
    perspective(PI / 3, width / height, 10, far);
  } else {
    ortho(-width / 2, width / 2,
          -height / 2, height / 2,
          10, far);
  }

  rotateX(-PI / 6);
  rotateY(PI / 3);

  box(180);
}

function mousePressed() {
  showPerspective = !showPerspective;
}
