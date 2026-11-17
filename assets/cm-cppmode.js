// CodeMirror mode for C++ Mode for Processing
// Matches Processing Java IDE keyword coloring:
//   FUNCTION1 = entry points / constructors (bold dark blue, paren-sensitive)
//   FUNCTION2 = API functions (light blue, always paren-sensitive)
//   KEYWORD3  = control flow (green)
//   KEYWORD4  = constants / variables (pink)
//   KEYWORD5  = types (orange)
//   KEYWORD6  = language keywords (teal)

(function(mod) {
  if (typeof exports == "object" && typeof module == "object") mod(require("codemirror"));
  else if (typeof define == "function" && define.amd) define(["codemirror"], mod);
  else mod(CodeMirror);
})(function(CodeMirror) {

// ── Keyword tables ────────────────────────────────────────────────────────────
// FUNCTION1: colored only when followed by ( -- entry points and color/PVector constructors
const FUNCTION1_PAREN = new Set([
  "color","PVector","PImage","PGraphics","PFont","PShape",
  "ArrayList","IntList","FloatList","StringList",
  "HashMap","HashSet",
]);
// FUNCTION1: always colored (setup/draw/event handlers)
const FUNCTION1_ALWAYS = new Set([
  "setup","draw","mousePressed","mouseReleased","mouseClicked",
  "mouseMoved","mouseDragged","mouseWheel",
  "keyPressed","keyReleased","keyTyped",
  "settings",
]);
// FUNCTION2: API functions -- colored only when followed by (
const FUNCTION2 = new Set([
  "size","fullScreen","smooth","noSmooth","frameRate","cursor","noCursor","exit",
  "background","fill","noFill","stroke","noStroke","strokeWeight","strokeCap","strokeJoin",
  "colorMode","lerpColor","red","green","blue","alpha","hue","saturation","brightness",
  "rect","ellipse","circle","square","line","point","triangle","quad","arc",
  "bezier","bezierVertex","bezierPoint","bezierTangent",
  "curve","curveVertex","curvePoint","curveTangent","curveTightness",
  "beginShape","endShape","vertex","curveVertex","bezierVertex","quadraticVertex",
  "pushMatrix","popMatrix","translate","rotate","rotateX","rotateY","rotateZ",
  "scale","shearX","shearY","resetMatrix","applyMatrix","printMatrix",
  "pushStyle","popStyle","push","pop",
  "image","imageMode","tint","noTint","texture","textureMode","textureWrap",
  "text","textSize","textAlign","textLeading","textWidth","textAscent","textDescent",
  "textFont","loadFont","createFont",
  "loadImage","requestImage","saveFrame","save",
  "loadPixels","updatePixels","get","set","copy","mask","filter","blend",
  "createGraphics","createImage","createShape",
  "lights","noLights","ambientLight","directionalLight","pointLight","spotLight",
  "lightFalloff","lightSpecular","normal","shininess","specular","emissive","ambient",
  "camera","perspective","ortho","frustum","printCamera","printProjection",
  "box","sphere","sphereDetail","beginCamera","endCamera",
  "noise","noiseDetail","noiseSeed","random","randomSeed","randomGaussian",
  "abs","ceil","floor","round","constrain","dist","lerp","mag","map","max","min","norm","sq","sqrt",
  "acos","asin","atan","atan2","cos","degrees","exp","log","pow","radians","sin","tan",
  "nf","nfc","nfp","nfs","hex","unhex","binary","unbinary",
  "str","int","boolean","byte","char","join","split","splitTokens","trim","toLowerCase","toUpperCase",
  "append","concat","expand","reverse","shorten","sort","splice","subset",
  "year","month","day","hour","minute","second","millis",
  "delay","print","println",
  "rectMode","ellipseMode","imageMode",
  "hint","blendMode","clip","noClip",
  "selectInput","selectOutput","selectFolder",
  "loadStrings","saveStrings","loadBytes","saveBytes",
  "loadJSON","saveJSON","loadXML","saveXML","loadTable","saveTable",
  "selectInput","selectOutput",
]);
// KEYWORD3: control flow -- always colored
const KEYWORD3 = new Set([
  "if","else","for","while","do","switch","case","break","continue","return",
  "default","goto","try","catch","throw","finally",
]);
// KEYWORD4: constants and built-in variables -- always colored
const KEYWORD4 = new Set([
  "PI","HALF_PI","QUARTER_PI","TWO_PI","TAU","E","DEG_TO_RAD","RAD_TO_DEG",
  "mouseX","mouseY","pmouseX","pmouseY","mouseDX","mouseDY",
  "mouseButton","mousePressed","keyPressed","keyCode","key",
  "width","height","frameCount","frameRate","displayWidth","displayHeight",
  "focused","_frameRate","deltaTime",
  "LEFT","RIGHT","CENTER","TOP","BOTTOM","BASELINE",
  "CORNER","CORNERS","RADIUS","CENTER",
  "POINTS","LINES","TRIANGLES","TRIANGLE_FAN","TRIANGLE_STRIP",
  "QUADS","QUAD_STRIP","CLOSE",
  "RGB","HSB","HSL","ARGB","ALPHA",
  "BLEND","ADD","SUBTRACT","DARKEST","LIGHTEST","DIFFERENCE",
  "EXCLUSION","MULTIPLY","SCREEN","OVERLAY","HARD_LIGHT","SOFT_LIGHT",
  "DODGE","BURN","REPLACE","REMOVE",
  "THRESHOLD","GRAY","INVERT","POSTERIZE","BLUR","OPAQUE","ERODE","DILATE",
  "OPEN","CHORD","PIE",
  "ROUND","SQUARE","PROJECT","MITER","BEVEL",
  "UP","DOWN","ALT","CONTROL","SHIFT","BACKSPACE","TAB","ENTER","RETURN",
  "ESC","DELETE","CODED","ARROW_LEFT","ARROW_RIGHT","ARROW_UP","ARROW_DOWN",
  "P2D","P3D","JAVA2D","PDF","SVG","DXF","FX2D",
  "ENABLE_DEPTH_TEST","DISABLE_DEPTH_TEST",
  "ENABLE_DEPTH_MASK","DISABLE_DEPTH_MASK",
  "true","false","null","nullptr","NULL",
  "WHITE","BLACK","RED","GREEN","BLUE","YELLOW","CYAN","MAGENTA",
]);
// KEYWORD5: types -- always colored
const KEYWORD5 = new Set([
  "color","PVector","PImage","PGraphics","PFont","PShape","PApplet",
  "ArrayList","IntList","FloatList","StringList","HashMap","HashSet",
  "int","float","double","boolean","bool","byte","char","long","short",
  "void","String","string","auto","size_t","uint32_t","uint8_t",
]);
// KEYWORD6: language keywords -- always colored
const KEYWORD6 = new Set([
  "class","struct","public","private","protected","virtual","override","final",
  "static","const","constexpr","inline","explicit","friend","operator",
  "new","delete","this","super","extends","implements","import","package",
  "namespace","using","typedef","typename","template","sizeof","alignof",
  "noexcept","decltype","nullptr","true","false",
  "include","define","ifdef","ifndef","endif","pragma",
]);

// ── Token class → CSS class mapping ──────────────────────────────────────────
// We emit custom token names that map to CSS via CodeMirror's token naming
// cm-keyword1 etc aren't standard; we use cm-def for FUNCTION1, etc.

CodeMirror.defineMode("cppmode", function(config) {
  var clikeMode = CodeMirror.getMode(config, "text/x-c++src");

  return {
    startState: function() {
      return {
        clike: CodeMirror.startState(clikeMode),
        lastToken: null,
        lastWord: null,
        parenNext: false,  // true if we just emitted a paren-sensitive word
        pendingWord: null, // word waiting to see if ( follows
        pendingType: null,
      };
    },

    copyState: function(state) {
      return {
        clike: CodeMirror.copyState(clikeMode, state.clike),
        lastToken: state.lastToken,
        lastWord: state.lastWord,
        parenNext: state.parenNext,
        pendingWord: state.pendingWord,
        pendingType: state.pendingType,
      };
    },

    token: function(stream, state) {
      // Skip whitespace
      if (stream.eatSpace()) {
        return null;
      }

      // Check for pending word -- did ( follow?
      if (state.pendingWord) {
        var ch = stream.peek();
        var word = state.pendingWord;
        var type = state.pendingType;
        state.pendingWord = null;
        state.pendingType = null;

        if (ch === '(') {
          // Yes -- emit as function
          return type === 'f1' ? 'cppmode-f1' : 'cppmode-f2';
        } else {
          // No paren -- if it's a dual type/function word, emit as type
          if (KEYWORD5.has(word)) return 'cppmode-k5';
          return null;
        }
      }

      var start = stream.pos;

      // Identifiers / keywords
      if (stream.match(/^[a-zA-Z_][a-zA-Z0-9_]*/)) {
        var word = stream.current();

        // KEYWORD3: control flow -- always
        if (KEYWORD3.has(word)) return 'cppmode-k3';

        // KEYWORD6: language keywords -- always
        if (KEYWORD6.has(word)) return 'cppmode-k6';

        // KEYWORD4: constants -- always
        if (KEYWORD4.has(word)) return 'cppmode-k4';

        // FUNCTION1 always (entry points)
        if (FUNCTION1_ALWAYS.has(word)) return 'cppmode-f1';

        // FUNCTION1 paren-sensitive (constructors)
        if (FUNCTION1_PAREN.has(word)) {
          // Peek ahead -- but we need to skip whitespace
          // Use pending mechanism
          state.pendingWord = word;
          state.pendingType = 'f1';
          // Consume this token now but defer color decision
          // We'll decide next token call
          return null; // temporarily uncolored -- will be resolved next call
        }

        // FUNCTION2: paren-sensitive API
        if (FUNCTION2.has(word)) {
          state.pendingWord = word;
          state.pendingType = 'f2';
          return null;
        }

        // KEYWORD5: types -- always (for things not in FUNCTION1_PAREN)
        if (KEYWORD5.has(word)) return 'cppmode-k5';

        // Fall through to clike for other identifiers
        stream.backUp(stream.current().length);
      }

      // Delegate to clike for everything else (strings, numbers, operators, etc.)
      var tok = clikeMode.token(stream, state.clike);
      return tok;
    },

    indent: function(state, textAfter) {
      return clikeMode.indent(state.clike, textAfter);
    },

    electricChars: clikeMode.electricChars,
    lineComment: clikeMode.lineComment,
    blockCommentStart: clikeMode.blockCommentStart,
    blockCommentEnd: clikeMode.blockCommentEnd,
    blockCommentContinue: clikeMode.blockCommentContinue,
    fold: "brace",
  };
});

CodeMirror.defineMIME("text/x-cppmode", "cppmode");

}); // end module
