/**
 * Multiple Particle Systems
 * by Daniel Shiffman.
 *
 * Click the mouse to generate a burst of particles
 * at mouse position.
 *
 * Each burst is one instance of a particle system
 * with Particles and CrazyParticles (a subclass of Particle).
 * Note use of Inheritance and Polymorphism.
 *
 * Rust has no subclasses: a trait says what every kind of particle can do,
 * and the list holds boxes of anything that has it.
 */
let mut systems: Vec<ParticleSystem> = Vec::new();

fn setup() {
    size(640, 360);
    systems = Vec::new();
}

fn draw() {
    background(0);
    for ps in systems.iter_mut() {
        ps.run();
        ps.add_particle();
    }
    if systems.is_empty() {
        fill(255);
        text_align(CENTER);
        text("click mouse to add particle systems", width() / 2.0, height() / 2.0);
    }
}

fn mouse_pressed() {
    systems.push(ParticleSystem::new(1, PVector::new(mouse_x(), mouse_y())));
}

// What every particle in a system can do
trait Runs {
    fn run(&mut self);
    fn is_dead(&self) -> bool;
}

// A particle built on Particle

#[derive(Clone, Default)]
struct CrazyParticle {
    particle: Particle,  // what CrazyParticle builds on (Java: extends Particle)
    theta: f32,
}

impl CrazyParticle {
    // Just adding one new variable to a CrazyParticle
    // It inherits all other fields from "Particle", and we don't have to retype them!
    // The CrazyParticle constructor can call the parent class (super class) constructor
    fn new(l: PVector) -> CrazyParticle {
        let mut this = CrazyParticle {
            particle: Particle::new(l),
            theta: 0.0,
        };
        // "super" means do everything from the constructor in Particle

        // One more line of code to deal with the new variable, theta
        this.theta = 0.0;
        this
    }

    // run() comes from the Runs trait below, as Particle's does
    // This update() method replaces the one in Particle
    fn update(&mut self) {
        self.particle.update();
        // Increment rotation based on horizontal velocity
        let theta_vel: f32 = (self.particle.velocity.x * self.particle.velocity.mag()) / 10.0;
        self.theta += theta_vel;
    }

    // This display() method replaces the one in Particle
    fn display(&self) {
        // Render the ellipse just like in a regular particle
        self.particle.display();
        // Then add a rotating line
        push_matrix();
        translate(self.particle.position.x, self.particle.position.y);
        rotate(self.theta);
        stroke(255, self.particle.lifespan);
        line(0.0, 0.0, 25.0, 0.0);
        pop_matrix();
    }
}

impl Runs for CrazyParticle {
    fn run(&mut self) {
        self.update();
        self.display();
    }
    fn is_dead(&self) -> bool { self.particle.is_dead() }
}

// A simple Particle class

#[derive(Clone, Default)]
struct Particle {
    position: PVector,
    velocity: PVector,
    acceleration: PVector,
    lifespan: f32,
}

impl Particle {
    fn new(l: PVector) -> Particle {
        Particle {
            position: l.copy(),
            velocity: PVector::new(random(-1.0, 1.0), random(-2.0, 0.0)),
            acceleration: PVector::new(0.0, 0.05),
            lifespan: 255.0,
        }
    }

    // Method to update position
    fn update(&mut self) {
        self.velocity.add(&self.acceleration);
        self.position.add(&self.velocity);
        self.lifespan -= 2.0;
    }

    // Method to display
    fn display(&self) {
        stroke(255, self.lifespan);
        fill(255, self.lifespan);
        ellipse(self.position.x, self.position.y, 8.0, 8.0);
    }

    // Is the particle still useful?
    fn is_dead(&self) -> bool {
        self.lifespan < 0.0
    }
}

impl Runs for Particle {
    fn run(&mut self) {
        self.update();
        self.display();
    }
    fn is_dead(&self) -> bool { Particle::is_dead(self) }
}

// An ArrayList is used to manage the list of Particles

struct ParticleSystem {
    particles: Vec<Box<dyn Runs>>,
    origin: PVector,
}

impl ParticleSystem {
    // An arraylist for all the particles
    // An origin point for where particles are birthed
    fn new(num: i32, v: PVector) -> ParticleSystem {
        let mut this = ParticleSystem {
            particles: Vec::new(),
            origin: PVector::new(0.0, 0.0),
        };
        // Initialize the arraylist
        this.origin = v.copy();  // Store the origin point
        for i in 0..num {
            this.particles.push(Box::new(Particle::new(this.origin)));  // Add "num" amount of particles to the arraylist
        }
        this
    }

    fn run(&mut self) {
        // Cycle through the ArrayList backwards, because we are deleting while iterating
        for i in (0..self.particles.len()).rev() {
            let p = &mut self.particles[i];
            p.run();
            if p.is_dead() {
                self.particles.remove(i);
            }
        }
    }

    fn add_particle(&mut self) {
        // Add either a Particle or CrazyParticle to the system
        let p: Box<dyn Runs> = if (random(0.0, 2.0) as i32) == 0 {
            Box::new(Particle::new(self.origin))
        } else {
            Box::new(CrazyParticle::new(self.origin))
        };
        self.particles.push(p);
    }

    // A method to test if the particle system still has particles
    fn dead(&self) -> bool {
        return self.particles.is_empty();
    }
}
