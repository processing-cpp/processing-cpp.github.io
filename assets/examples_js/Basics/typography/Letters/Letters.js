let f;

function setup() {
  createCanvas(640, 360);

  background(0);

  // Load font (make sure file exists in /assets or project folder)
  f = loadFont("SourceCodePro-Regular.ttf");

  textFont(f);
  textAlign(CENTER, CENTER);
  textSize(24);
}

function draw() {
  background(0);

  let margin = 10;

  translate(margin * 4, margin * 4);

  let gap = 46;
  let counter = 35;

  for (let y = 0; y < height - gap; y += gap) {
    for (let x = 0; x < width - gap; x += gap) {

      let letter = String.fromCharCode(counter);

      if (
        letter === "A" ||
        letter === "E" ||
        letter === "I" ||
        letter === "O" ||
        letter === "U"
      ) {
        fill(255, 204, 0);
      } else {
        fill(255);
      }

      text(letter, x, y);

      counter++;
    }
  }
}
