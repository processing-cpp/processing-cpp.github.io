let f;
let angleRotate = 0;

function setup() {
  createCanvas(640, 360);

  background(0);

  f = loadFont("SourceCodePro-Regular.ttf");

  textFont(f);
  textSize(18);
}

function draw() {
  background(0);

  strokeWeight(1);
  stroke(153);
  fill(255);

  push();

  let angle1 = radians(45);

  translate(100, 180);
  rotate(angle1);

  text("45 DEGREES", 0, 0);
  line(0, 0, 150, 0);

  pop();

  push();

  let angle2 = radians(270);

  translate(200, 180);
  rotate(angle2);

  text("270 DEGREES", 0, 0);
  line(0, 0, 150, 0);

  pop();

  push();

  translate(440, 180);
  rotate(radians(angleRotate));

  text(int(angleRotate % 360) + " DEGREES", 0, 0);

  line(0, 0, 150, 0);

  pop();

  angleRotate += 0.25;

  stroke(255, 0, 0);
  strokeWeight(4);

  point(100, 180);
  point(200, 180);
  point(440, 180);
}
