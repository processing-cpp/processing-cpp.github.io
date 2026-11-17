let rocket;
let rocketTex;
let ry = 0;

function preload() {
  rocket = loadModel("rocket.obj", true);
  rocketTex = loadImage("rocket.png");
}

function setup() {
  createCanvas(640, 360, WEBGL);
}

function draw() {
  background(0);
  lights();
  translate(0, 100, -200);
  rotateZ(PI);
  rotateY(ry);
  texture(rocketTex);
  model(rocket);
  ry += 0.02;
}
