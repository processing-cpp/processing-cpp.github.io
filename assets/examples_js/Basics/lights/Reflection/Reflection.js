function setup() {
  createCanvas(640, 360, WEBGL);
  noStroke();
}

function draw() {
  background(30);
  let s = mouseX / width;
  ambientLight(60);
  directionalLight(200, 200, 200, 0, 0, -1);
  specularMaterial(255 * s, 255 * s, 255 * s);
  shininess(100);
  fill(100, 100, 100);
  sphere(120);
}
