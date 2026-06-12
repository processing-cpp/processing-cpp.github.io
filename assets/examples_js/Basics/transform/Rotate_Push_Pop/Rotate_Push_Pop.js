let a = 0;
let offset = PI / 24.0;
let num = 12;

function setup() {
  createCanvas(640, 360, WEBGL);
  noStroke();
}

function draw() {
  background(0, 0, 26);
  ambientLight(60);
  directionalLight(255, 255, 255, 0, 0, -1);
  for (let i = 0; i < num; i++) {
    let gray = map(i, 0, num - 1, 0, 255);
    push();
    fill(gray);
    rotateY(a + offset * i);
    rotateX(a / 2 + offset * i);
    translate(0, 0, -50 * i);
    box(100);
    pop();
  }
  a += 0.01;
}
