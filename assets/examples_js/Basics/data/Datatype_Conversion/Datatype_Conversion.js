function setup() {
  createCanvas(640, 360);
  background(0);
  noStroke();

  textFont("monospace");
  textSize(24);
  fill(255);

  let c = 'A';
  let f = c.charCodeAt(0);
  let i = int(f * 1.4);
  let b = int(f / 2);

  text("The value of variable c is " + c, 50, 100);
  text("The value of variable f is " + f, 50, 150);
  text("The value of variable i is " + i, 50, 200);
  text("The value of variable b is " + b, 50, 250);

  noLoop();
}