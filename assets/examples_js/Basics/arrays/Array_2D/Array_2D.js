let distances;
let maxDistance;
let spacer;

function setup() {
  createCanvas(640, 360);
  maxDistance = dist(width / 2, height / 2, width, height);
  distances = new Array(width * height);

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      let distance = dist(width / 2, height / 2, x, y);
      distances[x + y * width] = distance / maxDistance * 255;
    }
  }

  spacer = 10;
  strokeWeight(6);
  noLoop();
}

function draw() {
  background(0);

  for (let y = 0; y < height; y += spacer) {
    for (let x = 0; x < width; x += spacer) {
      stroke(distances[x + y * width]);
      point(x + spacer / 2, y + spacer / 2);
    }
  }
}