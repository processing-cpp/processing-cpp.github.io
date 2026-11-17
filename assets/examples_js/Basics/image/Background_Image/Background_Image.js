let bg;
let y = 0;

function setup() {
  createCanvas(640, 360);

  bg = loadImage("moonwalk.jpg");
}

function draw() {
  background(bg);

  stroke(226, 204, 0);
  line(0, y, width, y);

  y++;

  if (y > height) {
    y = 0;
  }
}