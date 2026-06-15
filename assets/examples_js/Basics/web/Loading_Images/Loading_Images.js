let img;

function preload() {
  img = loadImage('https://processing-cpp.github.io/assets/data/processing-web.png');
}

function setup() {
  createCanvas(640, 360);
}

function draw() {
  background(0);
  if (img && img.width > 0) {
    let h = img.height * (640 / img.width); // scale to fit width
    for (let i = 0; i < 5; i++) {
      image(img, 0, h * i, 640, h);
    }
  } else {
    fill(255);
    textAlign(CENTER);
    textSize(14);
    text('Loading...', width/2, height/2);
  }
}
