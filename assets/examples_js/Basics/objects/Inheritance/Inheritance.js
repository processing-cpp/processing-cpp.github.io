class Spin {
  constructor(xpos, ypos, s) {
    this.x = xpos;
    this.y = ypos;
    this.speed = s;
    this.angle = 0.0;
  }

  update() {
    this.angle += this.speed;
  }
}

class SpinArm extends Spin {
  constructor(x, y, s) {
    super(x, y, s);
  }

  display() {
    strokeWeight(1);
    stroke(0);

    push();
    translate(this.x, this.y);

    rotate(this.angle);

    line(0, 0, 165, 0);

    pop();
  }
}

class SpinSpots extends Spin {
  constructor(x, y, s, d) {
    super(x, y, s);
    this.dim = d;
  }

  display() {
    noStroke();

    push();
    translate(this.x, this.y);

    rotate(this.angle);

    ellipse(-this.dim / 2, 0, this.dim, this.dim);
    ellipse(this.dim / 2, 0, this.dim, this.dim);

    pop();
  }
}

let spots;
let arm;

function setup() {
  createCanvas(640, 360);

  arm = new SpinArm(width / 2, height / 2, 0.01);
  spots = new SpinSpots(width / 2, height / 2, -0.02, 90.0);
}

function draw() {
  background(204);

  arm.update();
  arm.display();

  spots.update();
  spots.display();
}
