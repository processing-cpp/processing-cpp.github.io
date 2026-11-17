// Liquid class
class Liquid {
  constructor(x_, y_, w_, h_, c_) {
    this.x = x_;
    this.y = y_;
    this.w = w_;
    this.h = h_;
    this.c = c_;
  }

  // Is the Mover in the Liquid?
  contains(m) {
    let l = m.position;
    if (l.x > this.x && l.x < this.x + this.w && l.y > this.y && l.y < this.y + this.h) {
      return true;
    } else {
      return false;
    }
  }

  // Calculate drag force
  drag(m) {
    // Magnitude is coefficient * speed squared
    let speed = m.velocity.mag();
    let dragMagnitude = this.c * speed * speed;

    // Direction is inverse of velocity
    let drag = m.velocity.copy();
    drag.mult(-1);

    // Scale according to magnitude
    drag.setMag(dragMagnitude);
    return drag;
  }

  display() {
    noStroke();
    fill(127);
    rect(this.x, this.y, this.w, this.h);
  }
}

// Mover class
class Mover {
  constructor(m, x, y) {
    this.mass = m;
    this.position = createVector(x, y);
    this.velocity = createVector(0, 0);
    this.acceleration = createVector(0, 0);
  }

  // Newton's 2nd law: F = M * A
  // or A = F / M
  applyForce(force) {
    // Divide by mass
    let f = p5.Vector.div(force, this.mass);
    // Accumulate all forces in acceleration
    this.acceleration.add(f);
  }

  update() {
    // Velocity changes according to acceleration
    this.velocity.add(this.acceleration);
    // position changes by velocity
    this.position.add(this.velocity);
    // We must clear acceleration each frame
    this.acceleration.mult(0);
  }

  // Draw Mover
  display() {
    stroke(255);
    strokeWeight(2);
    fill(255, 200);
    ellipse(this.position.x, this.position.y, this.mass * 16, this.mass * 16);
  }

  // Bounce off bottom of window
  checkEdges() {
    if (this.position.y > height) {
      this.velocity.y *= -0.9;  // A little dampening when hitting the bottom
      this.position.y = height;
    }
  }
}

/**
 * Forces (Gravity and Fluid Resistance) with Vectors
 * by Daniel Shiffman.
 *
 * Demonstration of multiple forces acting on bodies.
 * Bodies experience gravity continuously and fluid
 * resistance when in "water".
 */

let movers = [];
let liquid;

function reset() {
  movers = [];
  for (let i = 0; i < 10; i++) {
    movers.push(new Mover(random(0.5, 3), 40 + i * 70, 0));
  }
}

function setup() {
  createCanvas(640, 360);
  reset();
  liquid = new Liquid(0, height / 2, width, height / 2, 0.1);
}

function draw() {
  background(0);

  liquid.display();

  for (let mover of movers) {
    // Is the Mover in the liquid?
    if (liquid.contains(mover)) {
      // Calculate drag force
      let drag = liquid.drag(mover);
      // Apply drag force to Mover
      mover.applyForce(drag);
    }

    // Gravity is scaled by mass here!
    let gravity = createVector(0, 0.1 * mover.mass);
    // Apply gravity
    mover.applyForce(gravity);

    // Update and display
    mover.update();
    mover.display();
    mover.checkEdges();
  }

  fill(255);
  text("click mouse to reset", 10, 30);
}

function mousePressed() {
  reset();
}
