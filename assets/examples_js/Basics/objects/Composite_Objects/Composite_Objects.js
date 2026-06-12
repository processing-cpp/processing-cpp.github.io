let er1;
let er2;

function setup() {
  createCanvas(640, 360);
  er1 = new EggRing(width * 0.45, height * 0.5, 2, 120);
  er2 = new EggRing(width * 0.65, height * 0.8, 10, 180);
}

function draw() {
  background(0);
  er1.transmit();
  er2.transmit();
}

class Egg {
  constructor(xpos, ypos, r, s) {
    this.x = xpos;
    this.y = ypos;
    this.tilt = 0;
    this.angle = 0;
    this.scalar = s / 100.0;
    this.range = r;
  }

  wobble() {
    this.tilt = cos(this.angle) / this.range;
    this.angle += 0.1;
  }

  display() {
    noStroke();
    fill(255);

    push();
    translate(this.x, this.y);
    rotate(this.tilt);
    scale(this.scalar);

    beginShape();
    vertex(0, -100);
    bezierVertex(25, -100, 40, -65, 40, -40);
    bezierVertex(40, -15, 25, 0, 0, 0);
    bezierVertex(-25, 0, -40, -15, -40, -40);
    bezierVertex(-40, -65, -25, -100, 0, -100);
    endShape(CLOSE);

    pop();
  }
}

class Ring {
  constructor() {
    this.x = 0;
    this.y = 0;
    this.diameter = 0;
    this.on = false;
  }

  start(xpos, ypos) {
    this.x = xpos;
    this.y = ypos;
    this.on = true;
    this.diameter = 1;
  }

  grow() {
    if (this.on) {
      this.diameter += 0.5;

      if (this.diameter > width * 2) {
        this.diameter = 0;
      }
    }
  }

  display() {
    if (this.on) {
      noFill();
      strokeWeight(4);
      stroke(155, 153);
      ellipse(this.x, this.y, this.diameter, this.diameter);
    }
  }
}

class EggRing {
  constructor(x, y, t, sp) {
    this.ovoid = new Egg(x, y, t, sp);
    this.circle = new Ring();

    this.circle.start(x, y - sp / 2);
  }

  transmit() {
    this.ovoid.wobble();
    this.ovoid.display();

    this.circle.grow();
    this.circle.display();

    if (!this.circle.on) {
      this.circle.on = true;
    }
  }
}
