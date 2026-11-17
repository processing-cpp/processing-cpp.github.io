let angles = [30, 10, 45, 35, 60, 38, 75, 67];
let anglesCount = angles.length;

function setup() {
  createCanvas(640, 360);
  noStroke();
  noLoop();
}

function draw() {
  background(100);
  pieChart(300, angles, anglesCount);
}

function pieChart(diameter, data, length) {
  let lastAngle = 0;

  for (let i = 0; i < length; i++) {
    let gray = map(i, 0, length, 0, 255);
    fill(gray);

    arc(
      width / 2,
      height / 2,
      diameter,
      diameter,
      lastAngle,
      lastAngle + radians(data[i])
    );

    lastAngle += radians(data[i]);
  }
}