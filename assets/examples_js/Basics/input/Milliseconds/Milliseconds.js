let _scale;

function setup() {
  createCanvas(640, 360);
  noStroke();
  _scale = width / 20.0;
}

function draw() {
  for (let i = 0; i < _scale; i++) {
    colorMode(RGB, (i + 1) * _scale * 10.0);

    fill(millis() % ((i + 1) * _scale * 10.0));

    rect(i * _scale, 0, _scale, height);
  }
}