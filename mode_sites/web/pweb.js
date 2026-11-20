// pweb.js: Processing's drawing functions in the browser, on top of p5.js.
// Shared by the Lua and Scheme web editors. The functions keep Processing's
// own rules, the way the desktop engine (RustMode's CPU renderer) does:
// colors are 32-bit ARGB numbers, images and fonts are numbers (handles),
// the constants have Processing's values, and pixels[] holds one color per
// pixel. Each mode's host puts these on its own globals.
(function (global) {
  "use strict";

  const K = {
    PI: Math.PI, TWO_PI: Math.PI * 2, HALF_PI: Math.PI / 2, TAU: Math.PI * 2, QUARTER_PI: Math.PI / 4,
    LEFT: 37, RIGHT: 39, CENTER: 3, TOP: 101, BOTTOM: 102, BASELINE: 0,
    CORNER: 0, CORNERS: 1, RADIUS: 2,
    OPEN: 1, CLOSE: 2, CHORD: 2, PIE: 3,
    REPLACE: 0, BLEND: 1, ADD: 2, SUBTRACT: 4, LIGHTEST: 8, DARKEST: 16, DIFFERENCE: 32,
    EXCLUSION: 64, MULTIPLY: 128, SCREEN: 256,
    RGB: 1, HSB: 3, ARGB: 2, ALPHA: 4,
    POINTS: 0, LINES: 1, TRIANGLES: 4, TRIANGLE_STRIP: 5, TRIANGLE_FAN: 6, QUADS: 7, QUAD_STRIP: 8, POLYGON: 9,
    SQUARE: 1, ROUND: 2, PROJECT: 4, MITER: 8, BEVEL: 32,
    BACKSPACE: 8, TAB: 9, ENTER: 10, RETURN: 13, ESC: 27, DELETE: 127, CODED: 0xFFFF,
    UP: 38, DOWN: 40, SHIFT: 16, CONTROL: 17, ALT: 18, NONE: 0,
    P2D: 2, P3D: 3, JAVA2D: 2, OPENGL: 3, IMAGE: 0, NORMAL: 1, CLAMP: 0, REPEAT: 1,
    BLUR: 11, GRAY: 12, INVERT: 13, OPAQUE: 14, POSTERIZE: 15, THRESHOLD: 16, ERODE: 17, DILATE: 18,
    ARROW: 0, CROSS: 1, TEXT: 2, WAIT: 3, HAND: 12, MOVE: 13,
  };
  const FONT_BASE = 1 << 24;

  // a color is a signed 32-bit int, 0xAARRGGBB, as in Processing
  const pack = (r, g, b, a) =>
    (((Math.round(a) & 255) << 24) | ((Math.round(r) & 255) << 16) | ((Math.round(g) & 255) << 8) | (Math.round(b) & 255)) | 0;
  const unpackC = (c) => [(c >> 16) & 255, (c >> 8) & 255, c & 255, (c >>> 24) & 255];
  const isPacked = (n) => Number.isInteger(n) && (n & 0xFF000000) !== 0;
  const clamp = (v, lo, hi) => (v < lo ? lo : v > hi ? hi : v);

  function PWeb(opts) {
    if (!(this instanceof PWeb)) return new PWeb(opts);
    const self = this;
    opts = opts || {};
    const dataBase = opts.dataBase || "";
    const print = opts.print || ((s) => console.log(s));
    const vfs = opts.files || {};          // name -> text, loaded before the sketch starts
    const pre = { images: {}, fonts: {} };  // preloaded by name
    let p = null, T = null;                 // the p5 instance, and what is drawn on (it or a layer)
    let is3D = false, mainW = 100, mainH = 100;
    let cm = { mode: K.RGB, max: [255, 255, 255, 255] };
    const handles = [null];                 // image / layer handles
    const fonts = [null];
    let stack = [];                          // layer begin/end
    let looping = true, targetFps = 60;
    let cb = {};                             // the sketch's callbacks
    let failed = false;
    let pixelsArr = null;                    // the canvas pixels[] the host hands out
    let imageModeV = K.CORNER;
    let tintOn = false;
    let shapeKind = null;

    const fail = (e) => { if (failed) return; failed = true; try { p && p.noLoop(); } catch (_) {} (opts.error || console.error)(e); };
    this.failed = () => failed;

    // ── colors ────────────────────────────────────────────────────────────
    function rgbaColor(c, t) {
      const [r, g, b, a] = unpackC(c);
      return (t || p).color("rgba(" + r + "," + g + "," + b + "," + a / 255 + ")");
    }
    // Processing's rules for color arguments (fill, stroke, background, color)
    function toColor(args, t) {
      t = t || T || p;
      const n = args.length;
      const a0 = args[0];
      if (n === 0) return t.color(0);
      if (a0 && typeof a0 === "object" && a0.levels) return a0;
      if (typeof a0 === "string") {
        const s = a0[0] === "#" && a0.length === 7 ? a0 : a0;
        const c = t.color(s);
        if (n >= 2) c.setAlpha(args[1] * 255 / cm.max[3]);
        return c;
      }
      if (n <= 2 && typeof a0 === "number" && (isPacked(a0) || a0 > cm.max[0] || a0 < 0)) {
        const c = rgbaColor(a0 | 0, t);
        if (n === 2) c.setAlpha(clamp(args[1] * 255 / cm.max[3], 0, 255));
        return c;
      }
      return t.color.apply(t, args.slice(0, 4));
    }
    const colorInt = (c) => pack(c.levels[0], c.levels[1], c.levels[2], c.levels[3]);
    const argColor = (v) => (typeof v === "number" ? (isPacked(v) ? v : colorInt(toColor([v]))) : colorInt(toColor([v])));

    // ── mapping Processing's numbers to p5's names ────────────────────────
    const M = () => ({
      mode: { 0: p.CORNER, 1: p.CORNERS, 2: p.RADIUS, 3: p.CENTER },
      halign: { 37: p.LEFT, 3: p.CENTER, 39: p.RIGHT },
      valign: { 101: p.TOP, 102: p.BOTTOM, 0: p.BASELINE, 3: p.CENTER },
      cap: { 1: p.SQUARE, 2: p.ROUND, 4: p.PROJECT },
      join: { 8: p.MITER, 32: p.BEVEL, 2: p.ROUND },
      arc: { 1: p.OPEN, 2: p.CHORD, 3: p.PIE },
      shape: { 0: p.POINTS, 1: p.LINES, 4: p.TRIANGLES, 5: p.TRIANGLE_STRIP, 6: p.TRIANGLE_FAN, 7: p.QUADS, 8: p.QUAD_STRIP },
      blend: { 0: p.REPLACE, 1: p.BLEND, 2: p.ADD, 4: p.SUBTRACT || p.BLEND, 8: p.LIGHTEST, 16: p.DARKEST,
               32: p.DIFFERENCE, 64: p.EXCLUSION, 128: p.MULTIPLY, 256: p.SCREEN },
      filter: { 11: p.BLUR, 12: p.GRAY, 13: p.INVERT, 14: p.OPAQUE, 15: p.POSTERIZE, 16: p.THRESHOLD, 17: p.ERODE, 18: p.DILATE },
      cursor: { 0: p.ARROW, 1: p.CROSS, 2: p.TEXT, 3: p.WAIT, 12: p.HAND, 13: p.MOVE },
    });
    let MP = null;

    // ── handles ───────────────────────────────────────────────────────────
    const newHandle = (o, kind) => { handles.push({ o: o, kind: kind }); return handles.length - 1; };
    const H = (id) => {
      const h = handles[id | 0];
      if (!h) throw new Error("not an image: " + id);
      return h;
    };
    const url = (name) => (/^(https?:|data:|blob:)/.test(name) ? name : dataBase + String(name).replace(/^data\//, ""));

    // ── pixels of a p5 image or the canvas as colors ──────────────────────
    function readPixels(o) {
      o.loadPixels();
      const d = o.pixels, n = (d.length / 4) | 0, out = new Array(n);
      for (let i = 0, j = 0; i < n; i++, j += 4) out[i] = pack(d[j], d[j + 1], d[j + 2], d[j + 3]);
      return out;
    }
    function writePixels(o, arr, get) {
      o.loadPixels();
      const d = o.pixels, n = (d.length / 4) | 0;
      for (let i = 0, j = 0; i < n; i++, j += 4) {
        let v = get ? get(i) : arr[i];
        if (v === undefined || v === null) continue;
        if (typeof v !== "number") v = argColor(v);
        else if (!isPacked(v)) { const g = clamp(Math.round(v * 255 / cm.max[0]), 0, 255); v = pack(g, g, g, 255); }
        d[j] = (v >> 16) & 255; d[j + 1] = (v >> 8) & 255; d[j + 2] = v & 255; d[j + 3] = (v >>> 24) & 255;
      }
      o.updatePixels();
    }

    // ── the API: Processing names ─────────────────────────────────────────
    const A = {};
    this.api = A;
    this.K = K;
    const t = () => T;

    A.size = (w, h, r) => {
      w = Math.max(1, Math.round(w)); h = Math.max(1, Math.round(h));
      mainW = w; mainH = h;
      is3D = r === K.P3D || r === "P3D" || r === 3;
      if (is3D) { p.createCanvas(w, h, p.WEBGL); p.translate(-w / 2, -h / 2); }
      else p.resizeCanvas(w, h);
      p.pixelDensity(1);
      T = p; applyDefaults();
      return [w, h];
    };
    A.fullScreen = () => A.size(window.innerWidth, window.innerHeight);
    A.is3D = () => is3D;
    function applyDefaults() { p.background(204); p.fill(255); p.stroke(0); p.strokeWeight(1); }
    A.smooth = () => {}; A.noSmooth = () => { try { T.noSmooth(); } catch (_) {} };
    A.pixelDensity = () => {}; A.displayDensity = () => 1;
    A.windowTitle = () => {}; A.windowResizable = () => {}; A.windowRatio = () => {};
    A.windowMove = () => {}; A.windowResize = (w, h) => A.size(w, h, is3D ? 3 : 2);
    A.cursor = (k) => { try { p.cursor(typeof k === "number" ? MP.cursor[k] : p.ARROW); } catch (_) {} };
    A.noCursor = () => p.noCursor();
    A.hint = () => {};
    A.displayWidth = () => window.screen.width; A.displayHeight = () => window.screen.height;

    // colors
    A.colorMode = (m, a, b, c, d) => {
      cm.mode = m;
      if (a !== undefined && b === undefined) cm.max = [a, a, a, a];
      else if (a !== undefined) cm.max = [a, b, c, d === undefined ? cm.max[3] : d];
      const args = [m === K.HSB ? p.HSB : p.RGB].concat(cm.max);
      T.colorMode.apply(T, args);
      if (T !== p) p.colorMode.apply(p, args);
    };
    A.color = (...a) => colorInt(toColor(a));
    A.red = (c) => unpackC(argColor(c))[0] * cm.max[0] / 255;
    A.green = (c) => unpackC(argColor(c))[1] * cm.max[1] / 255;
    A.blue = (c) => unpackC(argColor(c))[2] * cm.max[2] / 255;
    A.alpha = (c) => unpackC(argColor(c))[3] * cm.max[3] / 255;
    A.hue = (c) => p.hue(rgbaColor(argColor(c))) * (cm.mode === K.HSB ? cm.max[0] / 360 : 255 / 360);
    A.saturation = (c) => p.saturation(rgbaColor(argColor(c))) * (cm.mode === K.HSB ? cm.max[1] / 100 : 255 / 100);
    A.brightness = (c) => p.brightness(rgbaColor(argColor(c))) * (cm.mode === K.HSB ? cm.max[2] / 100 : 255 / 100);
    A.lerpColor = (a, b, amt) => colorInt(p.lerpColor(rgbaColor(argColor(a)), rgbaColor(argColor(b)), clamp(amt, 0, 1)));
    A.background = (...a) => {
      if (a.length === 1 && typeof a[0] === "number" && handles[a[0]] && !isPacked(a[0]) && a[0] > cm.max[0]) return T.background(H(a[0]).o);
      const c = toColor(a); T.background(c);
    };
    A.clear = () => T.clear();
    let curFill = "rgb(255,255,255)", curStroke = "rgb(0,0,0)";
    A.fill = (...a) => { const c = toColor(a); curFill = c.toString(); T.fill(c); };
    A.noFill = () => { curFill = "none"; T.noFill(); };
    A.stroke = (...a) => { const c = toColor(a); curStroke = c.toString(); T.stroke(c); };
    A.noStroke = () => { curStroke = "none"; T.noStroke(); };
    A.strokeWeight = (w) => T.strokeWeight(w);
    A.strokeCap = (c) => T.strokeCap(MP.cap[c] || p.ROUND);
    A.strokeJoin = (j) => T.strokeJoin(MP.join[j] || p.MITER);
    A.tint = (...a) => { tintOn = true; T.tint(toColor(a)); };
    A.noTint = () => { tintOn = false; T.noTint(); };
    A.blendMode = (m) => { try { T.blendMode(MP.blend[m] || p.BLEND); } catch (_) {} };

    // shapes
    A.rectMode = (m) => T.rectMode(MP.mode[m]);
    A.ellipseMode = (m) => T.ellipseMode(MP.mode[m]);
    A.imageMode = (m) => { imageModeV = m; T.imageMode(MP.mode[m]); };
    A.point = (...a) => T.point(...a);
    A.line = (...a) => T.line(...a);
    A.rect = (...a) => T.rect(...a);
    A.square = (x, y, s) => T.square(x, y, s);
    A.ellipse = (x, y, w, h) => T.ellipse(x, y, w, h === undefined ? w : h);
    A.circle = (x, y, d) => T.circle(x, y, d);
    A.triangle = (...a) => T.triangle(...a);
    A.quad = (...a) => T.quad(...a);
    A.arc = (x, y, w, h, a, b, m) => T.arc(x, y, w, h, a, b, m === undefined ? undefined : MP.arc[m]);
    A.bezier = (...a) => T.bezier(...a);
    A.curve = (...a) => T.curve(...a);
    A.bezierDetail = (d) => { try { T.bezierDetail(d); } catch (_) {} };
    A.curveDetail = (d) => { try { T.curveDetail(d); } catch (_) {} };
    A.curveTightness = (v) => T.curveTightness(v);
    A.bezierPoint = (a, b, c, d, u) => p.bezierPoint(a, b, c, d, u);
    A.bezierTangent = (a, b, c, d, u) => p.bezierTangent(a, b, c, d, u);
    A.curvePoint = (a, b, c, d, u) => p.curvePoint(a, b, c, d, u);
    A.curveTangent = (a, b, c, d, u) => p.curveTangent(a, b, c, d, u);
    A.beginShape = (k) => { shapeKind = k; T.beginShape(k === undefined || k === K.POLYGON ? undefined : MP.shape[k]); };
    A.endShape = (m) => T.endShape(m === K.CLOSE ? p.CLOSE : undefined);
    A.vertex = (...a) => T.vertex(...a);
    A.bezierVertex = (...a) => T.bezierVertex(...a);
    A.quadraticVertex = (...a) => T.quadraticVertex(...a);
    A.curveVertex = (...a) => T.curveVertex(...a);
    A.beginContour = () => T.beginContour();
    A.endContour = () => T.endContour();
    A.normal = (...a) => { try { T.normal(...a); } catch (_) {} };

    // transforms
    A.translate = (...a) => T.translate(...a);
    A.rotate = (a, x, y, z) => (x === undefined ? T.rotate(a) : T.rotate(a, [x, y, z]));
    A.rotateX = (a) => (is3D ? T.rotateX(a) : undefined);
    A.rotateY = (a) => (is3D ? T.rotateY(a) : undefined);
    A.rotateZ = (a) => (is3D ? T.rotateZ(a) : T.rotate(a));
    A.scale = (...a) => T.scale(...a);
    A.shearX = (a) => T.shearX(a);
    A.shearY = (a) => T.shearY(a);
    A.pushMatrix = () => T.push();
    A.popMatrix = () => T.pop();
    A.push = () => T.push();
    A.pop = () => T.pop();
    A.pushStyle = () => T.push();
    A.popStyle = () => T.pop();
    A.resetMatrix = () => { T.resetMatrix(); if (is3D && T === p) p.translate(-mainW / 2, -mainH / 2); };
    A.applyMatrix = (...a) => {
      if (a.length === 6) T.applyMatrix(a[0], a[3], a[1], a[4], a[2], a[5]);
      else if (a.length === 16) T.applyMatrix(a[0], a[4], a[8], a[12], a[1], a[5], a[9], a[13], a[2], a[6], a[10], a[14], a[3], a[7], a[11], a[15]);
    };
    A.printMatrix = () => print("[matrix]");

    // 3D
    A.box = (w, h, d) => T.box(w, h === undefined ? w : h, d === undefined ? w : d);
    A.sphere = (r) => T.sphere(r);
    A.sphereDetail = (u, v) => { A._sd = [u, v === undefined ? u : v]; };
    A.lights = () => { T.ambientLight(128); T.directionalLight(128, 128, 128, 0, 0, -1); };
    A.noLights = () => { try { T.noLights(); } catch (_) {} };
    A.ambientLight = (...a) => T.ambientLight(...a.slice(0, 3));
    A.directionalLight = (r, g, b, x, y, z) => T.directionalLight(r, g, b, x, y, z);
    A.pointLight = (r, g, b, x, y, z) => T.pointLight(r, g, b, x - (T === p && is3D ? 0 : 0), y, z);
    A.spotLight = (r, g, b, x, y, z, dx, dy, dz, angle, conc) => T.spotLight(r, g, b, x, y, z, dx, dy, dz, angle, conc);
    A.lightFalloff = (...a) => T.lightFalloff(...a);
    A.lightSpecular = (...a) => T.specularColor ? T.specularColor(...a) : undefined;
    A.ambient = (...a) => T.ambientMaterial(...a);
    A.specular = (...a) => T.specularMaterial(...a);
    A.emissive = (...a) => T.emissiveMaterial(...a);
    A.shininess = (s) => T.shininess(s);
    A.camera = (...a) => {
      if (a.length === 9) T.camera(a[0] - mainW / 2, a[1] - mainH / 2, a[2], a[3] - mainW / 2, a[4] - mainH / 2, a[5], a[6], a[7], a[8]);
      else T.camera();
    };
    A.perspective = (...a) => T.perspective(...a);
    A.ortho = (...a) => (a.length ? T.ortho(a[0] - mainW / 2, a[1] - mainW / 2, a[2] - mainH / 2, a[3] - mainH / 2, a[4], a[5]) : T.ortho());
    A.frustum = (...a) => T.frustum(...a);
    A.beginCamera = () => {}; A.endCamera = () => {}; A.printCamera = () => {}; A.printProjection = () => {};
    A.screenX = (x) => x; A.screenY = (x, y) => y; A.screenZ = () => 0;
    A.modelX = (x) => x; A.modelY = (x, y) => y; A.modelZ = (x, y, z) => z || 0;
    A.texture = (id) => T.texture(H(id).o);
    A.noTexture = () => {};
    A.textureMode = (m) => T.textureMode(m === K.NORMAL ? p.NORMAL : p.IMAGE);
    A.textureWrap = (m) => T.textureWrap(m === K.REPEAT ? p.REPEAT : p.CLAMP);

    // text
    let textFontId = 0;
    A.textSize = (s) => T.textSize(s);
    A.textAlign = (h, v) => T.textAlign(MP.halign[h] || p.LEFT, v === undefined ? p.BASELINE : MP.valign[v]);
    A.textLeading = (l) => T.textLeading(l);
    A.textWidth = (s) => T.textWidth(String(s));
    A.textAscent = () => T.textAscent();
    A.textDescent = () => T.textDescent();
    A.textMode = () => {};
    A.textStyle = () => {};
    A.text = (s, ...a) => {
      if (typeof s === "number" && !Number.isInteger(s)) s = s.toFixed(3).replace(/0+$/, "").replace(/\.$/, ".0");
      try { T.text(String(s), ...a); } catch (e) { if (!is3D) throw e; }
    };
    A.createFont = (name, size) => {
      const f = pre.fonts[name];
      fonts.push({ face: f || (/\.(ttf|otf|vlw)$/i.test(name) ? "sans-serif" : name), size: size || 12, name: name });
      return fonts.length - 1;
    };
    A.loadFont = (name) => A.createFont(name, 0);
    A.textFont = (id, size) => {
      const f = fonts[id | 0];
      textFontId = id | 0;
      if (f) T.textFont(f.face);
      if (size || (f && f.size)) T.textSize(size || f.size);
    };
    A.fontInfo = (id) => {
      const f = fonts[id | 0] || { size: 12, name: "SansSerif" };
      return [f.size, f.name, 0.8, 0.2];
    };
    A.fontCharWidth = (id, s) => { T.push(); A.textFont(id, 1); const w = T.textWidth(s); T.pop(); return w; };

    // images
    A.loadImage = (name) => {
      name = String(name);
      const hit = pre.images[name];
      if (hit) return newHandle(hit, "img");
      const img = p.createImage(1, 1);
      const id = newHandle(img, "img");
      p.loadImage(url(name), (ok) => { handles[id].o = ok; arrived(); }, () => print("loadImage: could not load " + name));
      return id;
    };
    A.requestImage = A.loadImage;
    A.createImage = (w, h) => newHandle(p.createImage(Math.max(1, w | 0), Math.max(1, h | 0)), "img");
    A.imageWidth = (id) => H(id).o.width;
    A.imageHeight = (id) => H(id).o.height;
    A.imgSize = (id) => { const h = handles[id | 0]; return h ? [h.o.width, h.o.height] : [0, 0]; };
    A.image = (id, x, y, w, h) => {
      const o = typeof id === "number" ? H(id).o : id;
      if (w === undefined) T.image(o, x, y); else T.image(o, x, y, w, h);
    };
    A.imageGet = (id, x, y, w, h) => {
      const o = H(id).o;
      if (w !== undefined) return newHandle(o.get(x | 0, y | 0, w | 0, h | 0), "img");
      const c = o.get(x | 0, y | 0);
      return pack(c[0], c[1], c[2], c[3]);
    };
    A.imgGet = (id, x, y) => A.imageGet(id, x, y);
    A.imageSet = (id, x, y, c) => { const o = H(id).o; o.set(x | 0, y | 0, rgbaColor(argColor(c))); o.updatePixels(); };
    A.imageCopy = (id) => { const o = H(id).o; return newHandle(o.get(), "img"); };
    A.imageResize = (id, w, h) => H(id).o.resize(w | 0, h | 0);
    A.imageMask = (id, m) => { H(id).o.mask(H(m).o); };
    A.imgLoadPixels = (id) => readPixels(H(id).o);
    A.imgUpdatePixels = (id, arr, get) => writePixels(H(id).o, arr, get);
    A.imagePixels = (id) => readPixels(H(id).o);
    A.imgFilter = (id, kind, param) => { const o = H(id).o; param === undefined || Number.isNaN(param) ? o.filter(MP.filter[kind]) : o.filter(MP.filter[kind], param); };
    A.imgBlend = (id, src, a, mode) => {
      const dst = H(id).o, s = H(src).o;
      if (mode === K.REPLACE) dst.copy(s, a[0], a[1], a[2], a[3], a[4], a[5], a[6], a[7]);
      else dst.blend(s, a[0], a[1], a[2], a[3], a[4], a[5], a[6], a[7], MP.blend[mode]);
    };
    A.imgSave = (id, path) => { try { H(id).o.save(String(path).replace(/\.[a-z]+$/i, ""), "png"); } catch (_) {} return true; };
    A.saveImage = A.imgSave;
    A.copy = (...a) => { if (a.length >= 8) T.copy(...a.slice(-8)); };
    A.blend = (...a) => { if (a.length >= 9) T.blend(...a.slice(-9, -1), MP.blend[a[a.length - 1]]); };
    A.filter = (kind, param) => (param === undefined || Number.isNaN(param) ? T.filter(MP.filter[kind]) : T.filter(MP.filter[kind], param));
    A.get = (x, y, w, h) => {
      if (x === undefined) return newHandle(T.get(), "img");
      if (w !== undefined) return newHandle(T.get(x | 0, y | 0, w | 0, h | 0), "img");
      const c = T.get(x | 0, y | 0);
      return pack(c[0], c[1], c[2], c[3] === undefined ? 255 : c[3]);
    };
    A.set = (x, y, c) => {
      if (typeof c === "number" && handles[c] && !isPacked(c) && c > cm.max[0]) { T.image(H(c).o, x, y); return; }
      const ctx = T.drawingContext;
      if (ctx && ctx.fillRect && !is3D) {
        const col = rgbaColor(argColor(c));
        ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.fillStyle = col.toString(); ctx.fillRect(x | 0, y | 0, 1, 1); ctx.restore();
      } else { T.set(x | 0, y | 0, rgbaColor(argColor(c))); T.updatePixels(); }
    };
    A.loadPixels = () => (pixelsArr = readPixels(T));
    A.updatePixels = (arr, get) => writePixels(T, arr || pixelsArr, get);
    A.pixelsArray = () => pixelsArr;

    // layers (createGraphics)
    A.createGraphics = (w, h, r) => {
      const g = p.createGraphics(Math.max(1, w | 0), Math.max(1, h | 0), r === K.P3D ? p.WEBGL : undefined);
      g.pixelDensity(1);
      g.clear();
      return newHandle(g, "gfx");
    };
    A.beginGraphics = (id) => { stack.push(T); T = H(id).o; return true; };
    A.endGraphics = () => { T = stack.pop() || p; };
    A.targetSize = () => [T.width, T.height];

    // SVG shapes (loadShape): drawn as pictures of the file; getChild()
    // makes a picture of just that part. With disableStyle() the parts take
    // the sketch's fill and stroke.
    const svgNS = "http://www.w3.org/2000/svg";
    function svgOf(text) {
      const doc = new DOMParser().parseFromString(text, "image/svg+xml");
      const root = doc.documentElement;
      let w = parseFloat(root.getAttribute("width")) || 0, h = parseFloat(root.getAttribute("height")) || 0;
      const vb = (root.getAttribute("viewBox") || "").split(/[\s,]+/).map(Number);
      if ((!w || !h) && vb.length === 4) { w = vb[2]; h = vb[3]; }
      if (w && h) { root.setAttribute("width", w); root.setAttribute("height", h); }
      const o = { doc, w, h, styled: true, cache: {} };
      o.img = picture(new XMLSerializer().serializeToString(doc));
      return [newHandle(o, "svg"), w, h];
    }
    // a sketch that stopped looping draws again once a late picture arrives
    const arrived = () => { if (!looping && !failed) p.redraw(); };
    function picture(text) { return p.loadImage(URL.createObjectURL(new Blob([text], { type: "image/svg+xml" })), arrived); }
    A.loadShape = (name) => {
      name = String(name);
      const text = vfs[name] !== undefined ? vfs[name] : vfs[name.replace(/^data\//, "")];
      if (text === undefined || !/<svg/i.test(text)) return [0, 0, 0];
      return svgOf(text);
    };
    A.shapeStyle = (id, on) => { const h0 = handles[id | 0]; if (h0) h0.o.styled = !!on; };
    A.shape = (id, x, y, w, h) => {
      const h0 = handles[id | 0]; if (!h0 || h0.kind !== "svg") return;
      const o = h0.o;
      let img = o.img;
      if (!o.styled) {
        const key = curFill + "|" + curStroke;
        if (!o.cache[key]) {
          const d = o.doc.cloneNode(true);
          d.querySelectorAll("*").forEach((el) => {
            if (el.style) { el.style.fill = ""; el.style.stroke = ""; }
            if (el.hasAttribute("fill") || /^(path|rect|circle|ellipse|polygon|polyline|line|g|text)$/.test(el.localName)) el.setAttribute("fill", curFill);
            el.setAttribute("stroke", curStroke);
          });
          o.cache[key] = picture(new XMLSerializer().serializeToString(d));
        }
        img = o.cache[key];
      }
      if (w === undefined) T.image(img, x || 0, y || 0, o.w, o.h); else T.image(img, x, y, w, h);
    };
    A.shapeChild = (id, key) => {
      const h0 = handles[id | 0]; if (!h0 || h0.kind !== "svg") return [0, 0, 0];
      // made once per part: sketches often ask for the same child every frame
      const memo = h0.o.children || (h0.o.children = {});
      const mkey = typeof key + ":" + key;
      if (memo[mkey]) return memo[mkey];
      return (memo[mkey] = childOf(h0, key));
    };
    function childOf(h0, key) {
      const root = h0.o.doc.documentElement;
      const el = typeof key === "number" ? [...root.children].filter((c) => c.localName !== "defs")[key | 0]
        : h0.o.doc.getElementById(String(key)) || root.querySelector('[id="' + String(key) + '"]');
      if (!el) return [0, 0, 0];
      const d = document.implementation.createDocument(svgNS, "svg", null);
      const r = d.documentElement;
      for (const at of root.attributes) r.setAttribute(at.name, at.value);
      root.querySelectorAll("defs").forEach((df) => r.appendChild(d.importNode(df, true)));
      r.appendChild(d.importNode(el, true));
      return svgOf(new XMLSerializer().serializeToString(d));
    }
    A.shapeChildCount = (id) => { const h0 = handles[id | 0]; return h0 && h0.kind === "svg" ? [...h0.o.doc.documentElement.children].filter((c) => c.localName !== "defs").length : 0; };
    // the outline points of a shape, as Processing's getVertex() sees them
    A.shapePoints = (id) => {
      const h0 = handles[id | 0]; if (!h0 || h0.kind !== "svg") return [];
      if (h0.o.points) return h0.o.points;
      const out = h0.o.points = [];
      h0.o.doc.querySelectorAll("path, polygon, polyline, line, rect").forEach((el) => {
        if (el.localName === "path") pathPoints(el.getAttribute("d") || "", out);
        else if (el.localName === "line") out.push({ x: +el.getAttribute("x1"), y: +el.getAttribute("y1") }, { x: +el.getAttribute("x2"), y: +el.getAttribute("y2") });
        else if (el.localName === "rect") { const x = +el.getAttribute("x") || 0, y = +el.getAttribute("y") || 0, w = +el.getAttribute("width"), h = +el.getAttribute("height"); out.push({ x, y }, { x: x + w, y }, { x: x + w, y: y + h }, { x, y: y + h }); }
        else { const n = (el.getAttribute("points") || "").trim().split(/[\s,]+/).map(Number); for (let i = 0; i + 1 < n.length; i += 2) out.push({ x: n[i], y: n[i + 1] }); }
      });
      return out;
    };
    function pathPoints(d, out) {
      const tok = d.match(/[a-zA-Z]|-?(?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?/g) || [];
      let i = 0, cmd = "", x = 0, y = 0, sx = 0, sy = 0;
      const n = () => parseFloat(tok[i++]);
      const counts = { M: 2, L: 2, H: 1, V: 1, C: 6, S: 4, Q: 4, T: 2, A: 7, Z: 0 };
      while (i < tok.length) {
        if (/[a-zA-Z]/.test(tok[i])) cmd = tok[i++];
        const C = cmd.toUpperCase(), rel = cmd !== C;
        if (C === "Z") { x = sx; y = sy; continue; }
        if (!(C in counts) || i + counts[C] > tok.length) break;
        const v = []; for (let k = 0; k < counts[C]; k++) v.push(n());
        if (C === "H") x = (rel ? x : 0) + v[0];
        else if (C === "V") y = (rel ? y : 0) + v[0];
        else { const ex = v[v.length - 2], ey = v[v.length - 1]; x = (rel ? x : 0) + ex; y = (rel ? y : 0) + ey; }
        if (C === "M") { sx = x; sy = y; if (cmd === "m") cmd = "l"; else cmd = "L"; }
        out.push({ x, y });
      }
    }

    // input and time
    A.millis = () => (p ? Math.round(p.millis()) : 0);
    A.frameCount = () => (p ? p.frameCount : 0);
    A.frameRate = (fps) => { if (fps !== undefined) { targetFps = fps; p.frameRate(fps); } return p ? p.frameRate() || targetFps : targetFps; };
    A.setFrameRate = (fps) => { targetFps = fps; p.frameRate(fps); return fps; };
    A.noLoop = () => { looping = false; p.noLoop(); };
    A.loop = () => { looping = true; p.loop(); };
    A.redraw = () => p.redraw();
    A.isLooping = () => looping;
    A.exit = () => { looping = false; p.noLoop(); if (opts.exit) opts.exit(); };
    A.delay = (ms) => { const end = performance.now() + ms; while (performance.now() < end) {} };
    A.saveFrame = (name) => { try { p.saveCanvas(String(name || "screen").replace(/#+/, (m) => String(p.frameCount).padStart(m.length, "0")).replace(/\.[a-z]+$/i, ""), "png"); } catch (_) {} };
    A.random = (a, b) => (b === undefined ? (a === undefined ? Math.random() : Math.random() * a) : a + Math.random() * (b - a));
    A.randomGaussian = () => p.randomGaussian();
    A.randomSeed = (s) => p.randomSeed(s);
    A.noise = (...a) => p.noise(...a);
    A.noiseDetail = (...a) => p.noiseDetail(...a);
    A.noiseSeed = (s) => p.noiseSeed(s);
    A.link = (u) => window.open(String(u), "_blank");
    A.launch = A.link;
    A.print = (s) => print(s);

    // what the sketch sees
    function keyChar() {
      const k = p.key;
      if (k === undefined || k === null) return "";
      if (k.length === 1) return k;
      return { Enter: "\n", Backspace: "\b", Tab: "\t", Escape: "\x1b", Delete: "\x7f" }[k] || K.CODED;
    }
    let pressedBtn = 0;
    this.state = () => ({
      mouseX: Math.round(p.mouseX), mouseY: Math.round(p.mouseY),
      pmouseX: Math.round(p.pmouseX), pmouseY: Math.round(p.pmouseY),
      mousePressed: p.mouseIsPressed, keyPressed: p.keyIsPressed,
      mouseButton: pressedBtn,
      key: keyChar(), keyCode: p.keyCode || 0,
      frameCount: p.frameCount, frameRate: p.frameRate() || targetFps,
      width: T ? T.width : mainW, height: T ? T.height : mainH, focused: p.focused !== false,
    });

    // ── running a sketch ──────────────────────────────────────────────────
    // host: { setup(), draw(), event(name, arg) } ; files to preload first
    this.run = function (parent, host, preload) {
      cb = host;
      new global.p5(function (pp) {
        p = pp; T = pp; MP = M();
        pp.preload = function () {
          (preload.images || []).forEach((n) => { pre.images[n] = pp.loadImage(url(n), () => {}, () => print("could not load " + n)); });
          (preload.fonts || []).forEach((n) => { pre.fonts[n] = pp.loadFont(url(n), () => {}, () => { pre.fonts[n] = null; }); });
        };
        pp.setup = function () {
          pp.createCanvas(100, 100);
          pp.pixelDensity(1);
          applyDefaults();
          pp.frameRate(60);
          try { host.setup(); } catch (e) { fail(e); }
        };
        pp.draw = function () {
          if (failed) return;
          if (is3D) pp.translate(-mainW / 2, -mainH / 2);
          try { host.draw(); } catch (e) { fail(e); }
        };
        const ev = (name, arg) => function (e) { if (failed) return; try { host.event(name, arg ? arg(e) : undefined); } catch (err) { fail(err); } };
        pp.mousePressed = function (e) { pressedBtn = { left: 37, right: 39, center: 3 }[pp.mouseButton] || 37; ev("mousePressed")(e); };
        pp.mouseReleased = ev("mouseReleased");
        pp.mouseClicked = ev("mouseClicked");
        pp.mouseMoved = ev("mouseMoved");
        pp.mouseDragged = ev("mouseDragged");
        pp.mouseWheel = function (e) { ev("mouseWheel", () => Math.sign(e.delta))(e); return false; };
        pp.keyPressed = function (e) { ev("keyPressed")(e); if ([32, 37, 38, 39, 40].includes(pp.keyCode)) return false; };
        pp.keyReleased = ev("keyReleased");
        pp.keyTyped = ev("keyTyped");
      }, parent);
    };
    this.p5 = () => p;
    this.FONT_BASE = FONT_BASE;
  }
  PWeb.K = K;
  PWeb.pack = pack;
  PWeb.isPacked = isPacked;
  global.PWeb = PWeb;
})(typeof window !== "undefined" ? window : globalThis);
