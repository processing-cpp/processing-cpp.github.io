let imgCount = 12;
let imgs = [];
let loadStates = [];
let imgW;

let loaderX = 0;
let loaderY = 0;
let theta = 0;

function checkLoadStates() {
  for (let i = 0; i < imgCount; i++) {
    if (!loadStates[i]) return false;
  }
  return true;
}

function drawImages() {
  let y = (height - imgs[0].height) / 2;

  for (let i = 0; i < imgCount; i++) {
    image(
      imgs[i],
      (width / imgCount) * i,
      y,
      imgs[i].height,
      imgs[i].height
    );
  }
}

function runLoaderAni() {
  if (!checkLoadStates()) {
    fill(255);
    noStroke();

    ellipse(loaderX, loaderY, 10, 10);

    loaderX += 2;
    loaderY = height / 2 + sin(theta) * (height / 8);
    theta += PI / 22;

    if (loaderX > width + 5) loaderX = -5;
  }
}

function setup() {
  createCanvas(640, 360);

  imgW = width / imgCount;

  for (let i = 0; i < imgCount; i++) {
    loadStates[i] = false;

    let path = "PT_anim" + nf(i, 4) + ".gif";
    imgs[i] = loadImage(path, () => {
      loadStates[i] = true;
    });
  }
}

function draw() {
  background(0);

  runLoaderAni();

  if (checkLoadStates()) {
    drawImages();
  }
}