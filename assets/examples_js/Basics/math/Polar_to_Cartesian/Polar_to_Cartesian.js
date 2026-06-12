let r;
let theta;
let theta_vel;
let theta_acc;

function setup() {
  createCanvas(640, 360);

  r = height * 0.45;
  theta = 0.0;
  theta_vel = 0.0;
  theta_acc = 0.0001;
}

function draw() {
  background(0);

  translate(width / 2, height / 2);

  let x = r * cos(theta);
  let y = r * sin(theta);

  ellipseMode(CENTER);
  noStroke();
  fill(200);
  ellipse(x, y, 32, 32);

  theta_vel += theta_acc;
  theta += theta_vel;
}