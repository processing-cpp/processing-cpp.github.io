let letter = "";
let words = "Begin...";

function setup() {
  createCanvas(640, 360);
  textFont("monospace");
}

function draw() {
  background(0);
  fill(255);
  textSize(14);
  text("Click on the program, then type to add to the String", 50, 50);
  text("Current key: " + letter, 50, 70);
  text("The String is " + words.length + " characters long", 50, 90);
  textSize(36);

  // manual wrap
  let lineWidth = 540;
  let x = 50;
  let y = 140;
  let lineHeight = 44;
  let line = "";
  for (let i = 0; i < words.length; i++) {
    let testLine = line + words[i];
    if (textWidth(testLine) > lineWidth) {
      text(line, x, y);
      y += lineHeight;
      line = words[i];
    } else {
      line = testLine;
    }
  }
  text(line, x, y);
}

function keyTyped() {
  if ((key >= 'A' && key <= 'z') || key === ' ') {
    letter = key;
    words += key;
  }
}
