// A simple Particle class, renders the particle as an image

class Particle {
  constructor(l, img_) {
    this.acc = createVector(0, 0);
    let vx = randomGaussian() * 0.3;
    let vy = randomGaussian() * 0.3 - 1.0;
    this.vel = createVector(vx, vy);
    this.loc = l.copy();
    this.lifespan = 100.0;
    this.img = img_;
  }

  run() {
    this.update();
    this.render();
  }

  // Method to apply a force vector to the Particle object
  // Note we are ignoring "mass" here
  applyForce(f) {
    this.acc.add(f);
  }

  // Method to update position
  update() {
    this.vel.add(this.acc);
    this.loc.add(this.vel);
    this.lifespan -= 2.5;
    this.acc.mult(0); // clear Acceleration
  }

  // Method to display
  render() {
    imageMode(CENTER);
    tint(255, this.lifespan);
    image(this.img, this.loc.x, this.loc.y);
    // Drawing a circle instead
    // fill(255, lifespan);
    // noStroke();
    // ellipse(loc.x, loc.y, img.width, img.height);
  }

  // Is the particle still useful?
  isDead() {
    if (this.lifespan <= 0.0) {
      return true;
    } else {
      return false;
    }
  }
}

// A class to describe a group of Particles
// An ArrayList is used to manage the list of Particles

class ParticleSystem {
  constructor(num, v, img_) {
    this.particles = [];
    this.origin = v.copy();
    this.img = img_;
    for (let i = 0; i < num; i++) {
      this.particles.push(new Particle(this.origin, this.img));
    }
  }

  run() {
    for (let i = this.particles.length - 1; i >= 0; i--) {
      let p = this.particles[i];
      p.run();
      if (p.isDead()) {
        this.particles.splice(i, 1);
      }
    }
  }

  // Method to add a force vector to all particles currently in the system
  applyForce(dir) {
    for (let p of this.particles) {
      p.applyForce(dir);
    }
  }

  addParticle() {
    this.particles.push(new Particle(this.origin, this.img));
  }
}

/**
 * Smoke Particle System
 * by Daniel Shiffman.
 *
 * A basic smoke effect using a particle system. Each particle
 * is rendered as an alpha masked image.
 */

let ps;

function setup() {
  createCanvas(640, 360);
  let img = loadImage("texture.png");
  ps = new ParticleSystem(0, createVector(width / 2, height - 60), img);
}

function draw() {
  background(0);

  // Calculate a "wind" force based on mouse horizontal position
  let dx = map(mouseX, 0, width, -0.2, 0.2);
  let wind = createVector(dx, 0);
  ps.applyForce(wind);
  ps.run();
  for (let i = 0; i < 2; i++) {
    ps.addParticle();
  }

  // Draw an arrow representing the wind force
  drawVector(wind, createVector(width / 2, 50), 500);
}

// Renders a vector object 'v' as an arrow and a position 'loc'
function drawVector(v, loc, scayl) {
  push();
  let arrowsize = 4;
  // Translate to position to render vector
  translate(loc.x, loc.y);
  stroke(255);
  // Call vector heading function to get direction (note that pointing up is a heading of 0) and rotate
  rotate(v.heading());
  // Calculate length of vector & scale it to be bigger or smaller if necessary
  let len = v.mag() * scayl;
  // Draw three lines to make an arrow (draw pointing up since we've rotated to the proper direction)
  line(0, 0, len, 0);
  line(len, 0, len - arrowsize, +arrowsize / 2);
  line(len, 0, len - arrowsize, -arrowsize / 2);
  pop();
}
