let a = 0;
let offset;
let num = 12;

function setup() {
  createCanvas(640, 360, WEBGL);
  noStroke();
  offset = PI / 24.0;
}

function draw() {
  background(0, 0, 26);
  ambientLight(150);
  directionalLight(255, 255, 255, 0, 0, -1);
  directionalLight(100, 100, 100, 0, 0, 1);

  for (let i = 0; i < num; i++) {
    let gray = map(i, 0, num - 1, 0, 255);
    push();
    fill(gray);
    rotateY(a + offset * i);
    rotateX(a / 2 + offset * i);
    box(90);
    pop();
  }
  a += 0.01;
}
