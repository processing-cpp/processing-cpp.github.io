let pg;

function setup() {
  createCanvas(640, 360);
  pg = createGraphics(400, 200);
}

function draw() {
  fill(0, 12);
  rect(0, 0, width, height);

  fill(255);
  noStroke();
  ellipse(mouseX, mouseY, 60, 60);

  pg.background(51);
  pg.noFill();
  pg.stroke(255);
  pg.ellipse(mouseX - 120, mouseY - 60, 60, 60);

  image(pg, 120, 60);
}
