/**
 * Koch Curve
 * by Daniel Shiffman.
 *
 * Renders a simple fractal, the Koch snowflake.
 * Each recursive level is drawn in sequence.
 */

// Koch Curve
// A class to describe one line segment in the fractal
// Includes methods to calculate midPVectors along the line according to the Koch algorithm
class KochLine {
    constructor(start, end) {
        this.a = start.copy();
        this.b = end.copy();
    }

    display() {
        stroke(255);
        line(this.a.x, this.a.y, this.b.x, this.b.y);
    }

    start() {
        return this.a.copy();
    }

    end() {
        return this.b.copy();
    }

    // This is easy, just 1/3 of the way
    kochleft() {
        let v = p5.Vector.sub(this.b, this.a);
        v.div(3);
        v.add(this.a);
        return v;
    }

    // More complicated, have to use a little trig to figure out where this PVector is!
    kochmiddle() {
        let v = p5.Vector.sub(this.b, this.a);
        v.div(3);

        let p = this.a.copy();
        p.add(v);

        v.rotate(-radians(60));
        p.add(v);

        return p;
    }

    // Easy, just 2/3 of the way
    kochright() {
        let v = p5.Vector.sub(this.a, this.b);
        v.div(3);
        v.add(this.b);
        return v;
    }
}

// Koch Curve
// A class to manage the list of line segments in the snowflake pattern
class KochFractal {
    constructor() {
        this.start = createVector(0, height - 20);
        this.end   = createVector(width, height - 20);
        this.count = 0;
        this.lines = [];
        this.restart();
    }

    nextLevel() {
        // For every line that is in the array
        // create 4 more lines in a new array
        this.lines = this.iterate(this.lines);
        this.count++;
    }

    restart() {
        this.count = 0;           // Reset count
        this.lines = [];          // Empty the array
        this.lines.push(new KochLine(this.start, this.end));  // Add the initial line
    }

    getCount() {
        return this.count;
    }

    // This is easy, just draw all the lines
    render() {
        for (let l of this.lines) {
            l.display();
        }
    }

    // This is where the **MAGIC** happens
    // Step 1: Create an empty array
    // Step 2: For every line currently in the array
    //   - calculate 4 line segments based on Koch algorithm
    //   - add all 4 line segments into the new array
    // Step 3: Return the new array and it becomes the list of line segments for the structure

    // As we do this over and over again, each line gets broken into 4 lines,
    // which gets broken into 4 lines, and so on. . .
    iterate(before) {
        let now = [];   // Create empty list
        for (let l of before) {
            // Calculate 5 koch PVectors (done for us by the line object)
            let a = l.start();
            let b = l.kochleft();
            let c = l.kochmiddle();
            let d = l.kochright();
            let e = l.end();
            // Make line segments between all the PVectors and add them
            now.push(new KochLine(a, b));
            now.push(new KochLine(b, c));
            now.push(new KochLine(c, d));
            now.push(new KochLine(d, e));
        }
        return now;
    }
}

let k;

function setup() {
    createCanvas(640, 360);
    frameRate(1);  // Animate slowly
    k = new KochFractal();
}

function draw() {
    background(0);
    // Draws the snowflake!
    k.render();
    // Iterate
    k.nextLevel();
    // Let's not do it more than 5 times. . .
    if (k.getCount() > 5) {
        k.restart();
    }
}
