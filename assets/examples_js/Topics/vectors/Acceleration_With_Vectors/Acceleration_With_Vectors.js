/**
 * Acceleration with Vectors
 * by Daniel Shiffman.
 *
 * Demonstration of the basics of motion with vector.
 * A "Mover" object stores location, velocity, and acceleration as vectors
 * The motion is controlled by affecting the acceleration (in this case towards the mouse)
 */

class Mover {
  constructor() {
    this.location = new p5.Vector(width/2, height/2);
    this.velocity = new p5.Vector(0, 0);
    this.topspeed = 5;
  }

  update() {
    let mouse = new p5.Vector(mouseX, mouseY);
    let acceleration = p5.Vector.sub(mouse, this.location);
    acceleration.setMag(0.2);
    this.velocity.add(acceleration);
    this.velocity.limit(this.topspeed);
    this.location.add(this.velocity);
  }

  display() {
    stroke(255);
    strokeWeight(2);
    fill(127);
    ellipse(this.location.x, this.location.y, 48, 48);
  }
}

/**
 * Acceleration with Vectors
 * by Daniel Shiffman.
 *
 * Demonstration of the basics of motion with vector.
 * A "Mover" object stores location, velocity, and
 * acceleration as vectors. The motion is controlled by
 * affecting the acceleration (in this case towards the mouse).
 */

let mover;

function setup() {
  createCanvas(640, 360);
  mover = new Mover();
}

function draw() {
  background(0);

  mover.update();
  mover.display();
}
