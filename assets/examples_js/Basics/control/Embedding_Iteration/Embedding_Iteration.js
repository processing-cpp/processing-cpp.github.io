function setup() {
  createCanvas(640, 360);
  background(0);

  let gridSize = 40;

  for (let x = gridSize; x <= width - gridSize; x += gridSize) {
    for (let y = gridSize; y <= height - gridSize; y += gridSize) {
      noStroke();
      fill(255);
      rect(x - 1, y - 1, 3, 3);

      stroke(255, 100);
      line(x, y, width / 2, height / 2);
    }
  }

  noLoop();
}