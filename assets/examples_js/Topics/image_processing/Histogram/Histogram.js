/**
 * Histogram.
 *
 * Calculates the histogram of an image.
 * A histogram is the frequency distribution
 * of the gray levels with the number of pure black values
 * displayed on the left and number of pure white values on the right.
 *
 * Note that this sketch will behave differently on Android,
 * since most images will no longer be full 24-bit color.
 */

createCanvas(640, 360);

// Load an image from the data directory
// Load a different image by modifying the comments
let img = loadImage("frontier.jpg");
image(img, 0, 0);
let hist = new Array(256).fill(0); // 256 zero-initialized entries

// Calculate the histogram
for (let i = 0; i < img.width; i++) {
  for (let j = 0; j < img.height; j++) {
    let bright = int(brightness(img.get(i, j)));
    hist[bright]++;
  }
}

// Find the largest value in the histogram
let histMax = Math.max(...hist);

stroke(255);
// Draw half of the histogram (skip every second value)
for (let i = 0; i < img.width; i += 2) {
  // Map i (from 0..img.width) to a location in the histogram (0..255)
  let which = int(map(i, 0, img.width, 0, 255));
  // Convert the histogram value to a location between
  // the bottom and the top of the picture
  let y = int(map(hist[which], 0, histMax, img.height, 0));
  line(i, img.height, i, y);
}
