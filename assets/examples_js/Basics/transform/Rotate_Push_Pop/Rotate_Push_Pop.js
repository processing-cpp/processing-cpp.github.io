let a = 0;
let offset = PI / 24.0;
let num = 12;

function setup() {
  createCanvas(640, 360, WEBGL);
  noStroke();
}

function draw() {
  background(0, 0, 26);
  for (let i = 0; i < num; i++) {
    push();
    normalMaterial();
    rotateY(a + offset * i);
    rotateX(a / 2 + offset * i);
    box(90);
    pop();
  }
  a += 0.01;
}
