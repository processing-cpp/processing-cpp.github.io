class Module {
  constructor(xOffset, yOffset, x, y, speed, unit) {
    this.xOffset = xOffset;
    this.yOffset = yOffset;
    this.x = x;
    this.y = y;
    this.unit = unit;
    this.xDirection = 1;
    this.yDirection = 1;
    this.speed = speed;
  }

  update() {
    this.x += this.speed * this.xDirection;

    if (this.x >= this.unit || this.x <= 0) {
      this.xDirection *= -1;
      this.x += this.xDirection;
      this.y += this.yDirection;
    }

    if (this.y >= this.unit || this.y <= 0) {
      this.yDirection *= -1;
      this.y += this.yDirection;
    }
  }

  display() {
    fill(255);
    ellipse(this.xOffset + this.x, this.yOffset + this.y, 6, 6);
  }
}

let unit = 40;
let count;
let mods;

function setup() {
  createCanvas(640, 360);
  noStroke();

  let wideCount = floor(width / unit);
  let highCount = floor(height / unit);

  count = wideCount * highCount;
  mods = [];

  for (let y = 0; y < highCount; y++) {
    for (let x = 0; x < wideCount; x++) {
      mods.push(
        new Module(
          x * unit,
          y * unit,
          unit / 2,
          unit / 2,
          random(0.05, 0.8),
          unit
        )
      );
    }
  }
}

function draw() {
  background(0);

  for (let i = 0; i < count; i++) {
    mods[i].update();
    mods[i].display();
  }
}