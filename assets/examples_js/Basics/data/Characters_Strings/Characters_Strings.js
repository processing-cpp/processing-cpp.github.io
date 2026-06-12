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
  text(words, 50, 120, 540, 300);
}

function keyTyped() {
  if ((key >= 'A' && key <= 'z') || key === ' ') {
    letter = key;
    words += key;
    console.log(key);
  }
}