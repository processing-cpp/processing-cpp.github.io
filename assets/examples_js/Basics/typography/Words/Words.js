let f;

function setup() {
  createCanvas(640, 360);

  // Load font (must exist in project folder or /assets)
  f = loadFont("SpaceMono-Regular.ttf");

  textFont(f);
  textSize(18);
}

function draw() {
  background(102);

  textAlign(RIGHT);
  drawType(width * 0.25);

  textAlign(CENTER);
  drawType(width * 0.5);

  textAlign(LEFT);
  drawType(width * 0.75);
}

function drawType(x) {
  line(x, 0, x, 65);
  line(x, 220, x, height);

  fill(0);
  text("ichi", x, 95);

  fill(51);
  text("ni", x, 130);

  fill(204);
  text("san", x, 165);

  fill(255);
  text("shi", x, 210);
}
