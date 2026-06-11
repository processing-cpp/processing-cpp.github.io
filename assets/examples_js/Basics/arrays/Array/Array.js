/**
 * Array.
 *
 * An array is a list of data. Each piece of data in an array
 * is identified by an index number representing its position in
 * the array. Arrays are zero based, which means that the first
 * element in the array is [0], the second element is [1], and so on.
 * In this example, an array named "coswave" is created and
 * filled with the cosine values. This data is displayed three
 * separate ways on the screen.
 */

let coswave = [];

p.setup = function() {
  p.createCanvas(640, 360);
  for (let i = 0; i < p.width; i++) {
    let amount = p.map(i, 0, p.width, 0, p.PI);
    coswave[i] = p.abs(p.cos(amount));
  }
  p.background(255);
  p.noLoop();
};

p.draw = function() {
  let y1 = 0;
  let y2 = p.height / 3;
  for (let i = 0; i < p.width; i++) {
    p.stroke(coswave[i] * 255);
    p.line(i, y1, i, y2);
  }

  y1 = y2;
  y2 = y1 + y1;
  for (let i = 0; i < p.width; i++) {
    p.stroke(coswave[i] * 255 / 4);
    p.line(i, y1, i, y2);
  }

  y1 = y2;
  y2 = p.height;
  for (let i = 0; i < p.width; i++) {
    p.stroke(255 - coswave[i] * 255);
    p.line(i, y1, i, y2);
  }
};
