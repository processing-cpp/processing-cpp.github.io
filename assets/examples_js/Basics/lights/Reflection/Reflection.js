function setup() {
  createCanvas(640, 360, WEBGL);
  noStroke();
  colorMode(RGB, 1);
  fill(0.4);
}

function draw() {
  background(0);

  lightSpecular(1.0, 1.0, 1.0);
  directionalLight(0.8, 0.8, 0.8, 0, 0, -1);

  let s = mouseX / width;

  specular(s, s, s);

  sphere(120);
}