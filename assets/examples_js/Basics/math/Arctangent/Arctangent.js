class Eye {
  constructor(x, y, size) {
    this.x = x;
    this.y = y;
    this.size = size;
    this.angle = 0.0;
  }

  update(mx, my) {
    this.angle = atan2(my - this.y, mx - this.x);
  }

  display() {
    push();

    translate(this.x, this.y);

    fill(255);
    noStroke();
    ellipse(0, 0, this.size, this.size);

    rotate(this.angle);

    fill(153, 204, 0);
    ellipse(this.size / 4, 0, this.size / 2, this.size / 2);

    pop();
  }
}

let e1;
let e2;
let e3;

function setup() {
  createCanvas(640, 360);
  noStroke();

  e1 = new Eye(250, 16, 120);
  e2 = new Eye(164, 185, 80);
  e3 = new Eye(420, 230, 220);
}

function draw() {
  background(102);

  e1.update(mouseX, mouseY);
  e1.display();

  e2.update(mouseX, mouseY);
  e2.display();

  e3.update(mouseX, mouseY);
  e3.display();
}
