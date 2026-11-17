let img;
let smallPoint, largePoint;

function setup() {
  createCanvas(640, 360);

  img = loadImage("moonwalk.jpg");

  smallPoint = 4;
  largePoint = 40;

  imageMode(CENTER);
  noStroke();
  background(255);
}

function draw() {
  let pointillize = map(mouseX, 0, width, smallPoint, largePoint);

  let x = floor(random(img.width));
  let y = floor(random(img.height));

  let pix = img.get(x, y);

  fill(red(pix), green(pix), blue(pix), 128);
  ellipse(x, y, pointillize, pointillize);
}