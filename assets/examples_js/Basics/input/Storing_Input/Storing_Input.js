let num = 60;
let mx = [];
let my = [];

function setup() {
  createCanvas(640, 360);
  noStroke();
  fill(255, 153);

  for (let i = 0; i < num; i++) {
    mx[i] = 0;
    my[i] = 0;
  }
}

function draw() {
  background(51);

  let which = frameCount % num;

  mx[which] = mouseX;
  my[which] = mouseY;

  for (let i = 0; i < num; i++) {
    let index = (which + 1 + i) % num;
    ellipse(mx[index], my[index], i, i);
  }
}