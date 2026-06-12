class Spot {
  constructor(xpos = width * 0.25, ypos = height * 0.5, r = 40) {
    this.x = xpos;
    this.y = ypos;
    this.radius = r;
  }

  display() {
    ellipse(this.x, this.y, this.radius * 2, this.radius * 2);
  }
}

let sp1;
let sp2;

function setup() {
  createCanvas(640, 360);

  background(204);
  noLoop();

  // Equivalent to Spot()
  sp1 = new Spot();

  // Equivalent to Spot(float xpos, float ypos, float r)
  sp2 = new Spot(width * 0.5, height * 0.5, 120);
}

function draw() {
  sp1.display();
  sp2.display();
}
