"""Copy that differs between the C++ site and the Lua / Rust sites.

CONTENT[key][page] replaces the whole <div class="content"> of a page.
TEXT[key] is a list of (C++ site text, mode text) swapped before the
generic rebrand. DROP[key] are pages the mode has no equivalent for.
"""

C = 'style="font-family:monospace;background:#f4f4f4;padding:1px 5px;border-radius:3px;"'

REPO = {"lua": "https://github.com/llamasjc/processing-lua", "rust": "https://github.com/llamasjc/processing-rust"}

FIRST = {
    "lua": """function setup()
  size(640, 360)
end

function draw()
  background(20)
  ellipse(mouseX, mouseY, 40, 40)
end""",
    "rust": """fn setup() {
    size(640, 360);
}

fn draw() {
    background(20);
    ellipse(mouse_x(), mouse_y(), 40.0, 40.0);
}""",
}

CPP_FIRST = """void setup() {
  size(640, 360);
}

void draw() {
  background(20);
  ellipse(mouseX, mouseY, 40, 40);
}"""


def install_steps(key):
    name = {"lua": "Lua", "rust": "Rust"}[key]
    return f"""<ol class="step-list">
        <li>Download the {name} Mode zip from the <a href="{REPO[key]}/releases/latest" style="border-bottom:1px solid #ddd;">latest release</a>.</li>
        <li>Unzip it into the <strong>modes</strong> folder of your sketchbook (Processing shows where the sketchbook is in <strong>File &gt; Preferences</strong>), so you have <code>sketchbook/modes/{name}Mode</code>.</li>
        <li>Restart Processing and pick <strong>{name}</strong> from the mode dropdown in the top-right of the editor.</li>
      </ol>"""


TUTORIALS = {
    "lua": f"""<div class="content">
    <h1>Tutorials</h1>
    <p class="subtitle">Lua Mode is a plugin for the Processing IDE. You write sketches in Lua inside Processing, hit Run, and a window opens. Pick the section that matches what you're trying to do.</p>

    <div class="path">
      <h2>Using Lua Mode inside the Processing IDE</h2>
      <p class="section-desc">Write <code {C}>setup()</code> and <code {C}>draw()</code> as Lua functions, hit Run, and see a window open. Your sketch runs on a small native runner with the same drawing engine as Rust Mode, so there is nothing to compile and it starts right away.</p>

      <a class="tutorial-card" href="/gettingstarted">
        <div class="tc-body">
          <div class="tc-title">Getting Started with Lua Mode</div>
          <div class="tc-desc">How to install Lua Mode and write your first sketch in the Processing IDE.</div>
        </div>
        <div class="tc-arrow">›</div>
      </a>

      <a class="tutorial-card" href="/downloads#lua-mode">
        <div class="tc-body">
          <div class="tc-title">Installing the mode</div>
          <div class="tc-desc">Where to download Lua Mode and where to put it.</div>
        </div>
        <div class="tc-arrow">›</div>
      </a>

      <a class="tutorial-card" href="/whats-new">
        <div class="tc-body">
          <div class="tc-title">Coming from Processing Java</div>
          <div class="tc-desc">The few things that change when the same sketch is written in Lua.</div>
        </div>
        <div class="tc-arrow">›</div>
      </a>
    </div>

    <div class="path">
      <h2>Sharing what you made</h2>
      <p class="section-desc"><strong>File &gt; Export Application</strong> makes a folder with your sketch, its data folder and the runner, ready to run on a computer without Processing. <strong>File &gt; Export as PDEZ</strong> packs the sketch into one file another Processing user can open.</p>
    </div>

    <div class="help-box">
      <p>New to all of this? Start with <a href="/gettingstarted">Getting Started</a>, then open any of the <a href="/examples">examples</a>. Every one of them is the Processing example you may already know, written in Lua.</p>
    </div>
  </div>""",
    "rust": f"""<div class="content">
    <h1>Tutorials</h1>
    <p class="subtitle">Rust Mode comes in two forms. One is a plugin for the Processing IDE, which lets you write sketches inside Processing itself just like you normally would. The other is the engine as a Rust crate you can use in any Cargo project. Pick the section that matches what you're trying to do.</p>

    <div class="path">
      <h2>Using Rust Mode inside the Processing IDE</h2>
      <p class="section-desc">Write <code {C}>setup()</code> and <code {C}>draw()</code> as Rust functions, hit Run, and see a window open. Rust Mode turns your sketch into a small Rust program and compiles it against a prebuilt engine, so after the first run it only rebuilds your code.</p>

      <a class="tutorial-card" href="/gettingstarted">
        <div class="tc-body">
          <div class="tc-title">Getting Started with Rust Mode</div>
          <div class="tc-desc">How to install Rust Mode and write your first sketch in the Processing IDE.</div>
        </div>
        <div class="tc-arrow">›</div>
      </a>

      <a class="tutorial-card" href="/downloads#rust-mode">
        <div class="tc-body">
          <div class="tc-title">Installing the mode</div>
          <div class="tc-desc">Where to download Rust Mode, where to put it, and what Rust it needs.</div>
        </div>
        <div class="tc-arrow">›</div>
      </a>

      <a class="tutorial-card" href="/whats-new">
        <div class="tc-body">
          <div class="tc-title">Coming from Processing Java</div>
          <div class="tc-desc">The things that change when the same sketch is written in Rust.</div>
        </div>
        <div class="tc-arrow">›</div>
      </a>
    </div>

    <div class="path">
      <h2>Using the engine in your own Rust project</h2>
      <p class="section-desc">The engine is a normal crate. Add it to <code {C}>Cargo.toml</code>, write a <code {C}>main()</code> that hands it your state and your setup and draw functions, and build with <code {C}>cargo run</code>. See <a href="/downloads#crate" style="border-bottom:1px solid #ddd;">the crate</a> on the Downloads page.</p>
    </div>

    <div class="help-box">
      <p>Still not sure which one fits? If you know Processing and just want to keep working the same way, go with <a href="/gettingstarted">Getting Started</a>. If you already have a Cargo project, use <a href="/downloads#crate">the crate</a>.</p>
    </div>
  </div>""",
}

DOWNLOADS = {
    "lua": f"""<div class="content">
    <h1>Downloads</h1>
    <p class="subtitle">Lua Mode is one zip. It has the mode, the runner for your computer and the examples.</p>

    <div class="mode-callout" id="lua-mode">
      <h2>Installing Lua Mode</h2>
      <p>Lua Mode isn't in the Contribution Manager yet, so it's installed by hand. It takes a minute.</p>
      {install_steps("lua")}
      <p>To draw with the libprocessing renderer (Bevy and wgpu, on your graphics card) pick it from the renderer menu in the toolbar. The default renderer draws on the CPU and needs nothing else.</p>
    </div>

    <h2>The source</h2>
    <p>Lua Mode is open source. The code, the issues and every release are on <a href="{REPO['lua']}" style="border-bottom:1px solid #ddd;">GitHub</a>.</p>
  </div>""",
    "rust": f"""<div class="content">
    <h1>Downloads</h1>
    <p class="subtitle">Two ways to get Rust Mode, depending on how you want to work.</p>

    <div class="mode-callout" id="rust-mode">
      <h2>Installing Rust Mode</h2>
      <p>Rust Mode isn't in the Contribution Manager yet, so it's installed by hand. You also need Rust itself: get it from <a href="https://rustup.rs" style="border-bottom:1px solid #ddd;">rustup.rs</a> if you don't have it.</p>
      {install_steps("rust")}
      <p>The zip comes with the engine already compiled for some computers, so your first Run is quick there. On the others the first Run builds the engine once, which takes a few minutes.</p>
    </div>

    <h2 id="crate">The engine as a crate</h2>
    <p>For writing plain Rust in your own editor, with no Processing IDE involved. Add the engine to your <code>Cargo.toml</code>:</p>
    <pre><code>[dependencies]
processing = {{ git = "{REPO['rust']}" }}</code></pre>
    <p>and give it your sketch:</p>
    <pre><code>use processing::*;

struct Sketch {{ x: f32 }}

fn setup(s: &amp;mut Sketch) {{
    size(640, 360);
}}

fn draw(s: &amp;mut Sketch) {{
    background(20);
    s.x = (s.x + 2.0) % width();
    ellipse(s.x, height() / 2.0, 40.0, 40.0);
}}

fn main() {{
    App::new(Sketch {{ x: 0.0 }}, setup, draw).run();
}}</code></pre>
    <p>Then <code>cargo run</code>. The code and every release are on <a href="{REPO['rust']}" style="border-bottom:1px solid #ddd;">GitHub</a>.</p>
  </div>""",
}

LIB = lambda code, text, href=None: (f'<div class="lib-card"><code>' + (f'<a href="{href}" target="_blank" rel="noopener" style="color:inherit;text-decoration:none;border-bottom:1px solid #ddd;">{code}</a>' if href else code) + f'</code><p>{text}</p></div>')

LIBRARIES = {
    "lua": "<div class=\"content\">\n <h1>Libraries</h1>\n <p class=\"subtitle\">Everything available in Lua Mode out of the box.</p>\n\n <div class=\"tip\">\n None of these need a <code>require</code>. They are in every sketch from the start.\n </div>\n\n"
    + " <h2>Lua's own libraries</h2>\n <div class=\"lib-grid\">\n " + "\n ".join([
        LIB("table", "Lists and maps in one. table.insert, table.remove, table.sort, table.concat.", "https://www.lua.org/manual/5.4/manual.html#6.6"),
        LIB("string", "Text. string.format, :sub, :find, :gsub, :upper, patterns.", "https://www.lua.org/manual/5.4/manual.html#6.4"),
        LIB("math", "math.floor, math.huge, math.pi and the rest. Processing's own sin(), abs() and friends work too.", "https://www.lua.org/manual/5.4/manual.html#6.7"),
        LIB("utf8", "Text with accents and other non-ASCII letters.", "https://www.lua.org/manual/5.4/manual.html#6.5"),
        LIB("os", "os.time, os.date, os.clock.", "https://www.lua.org/manual/5.4/manual.html#6.9"),
        LIB("io", "Reading and writing files, if loadStrings() isn't enough.", "https://www.lua.org/manual/5.4/manual.html#6.8"),
        LIB("coroutine", "Functions that can pause and pick up later. Handy for animations that run in steps.", "https://www.lua.org/manual/5.4/manual.html#6.2"),
    ]) + "\n </div>\n\n <h2>Processing's classes</h2>\n <div class=\"lib-grid\">\n " + "\n ".join([
        LIB("PVector", "2D and 3D vectors: v:add(w), v:mag(), v:normalize(), and + - * / between vectors.", "/reference/PVector.html"),
        LIB("IntList / FloatList / StringList", "Processing's lists, with sort(), shuffle(), sum() and the rest."),
        LIB("IntDict / FloatDict / StringDict", "Processing's dictionaries."),
        LIB("Table / TableRow", "CSV and TSV files: loadTable(), t:getRowCount(), row:getFloat(\"x\")."),
        LIB("JSON", "loadJSONObject(), loadJSONArray() and saveJSONObject(). JSON comes in as plain Lua tables."),
        LIB("XML", "loadXML(), xml:getChildren(\"item\"), xml:getString(\"name\")."),
        LIB("PImage / PGraphics", "Images and off-screen layers: img:get(x, y), img.pixels, pg:beginDraw()."),
        LIB("PShape / PFont / PShader", "SVG and OBJ shapes, fonts, and GLSL shaders."),
    ]) + "\n </div>\n </div>",
    "rust": "<div class=\"content\">\n <h1>Libraries</h1>\n <p class=\"subtitle\">Everything available in Rust Mode out of the box.</p>\n\n <div class=\"tip\">\n None of these need a <code>use</code> line. Rust's standard library is always there, and every sketch starts with <code>use processing::*;</code> for you.\n </div>\n\n"
    + " <h2>Rust's standard library</h2>\n <div class=\"lib-grid\">\n " + "\n ".join([
        LIB("Vec", "Growable list. The one to use instead of Java's arrays and ArrayList.", "https://doc.rust-lang.org/std/vec/struct.Vec.html"),
        LIB("HashMap / BTreeMap", "Key-value maps: std::collections::HashMap. BTreeMap keeps the keys sorted.", "https://doc.rust-lang.org/std/collections/index.html"),
        LIB("HashSet / BTreeSet", "Collections of unique values.", "https://doc.rust-lang.org/std/collections/index.html"),
        LIB("VecDeque", "A queue you can add to and take from at both ends.", "https://doc.rust-lang.org/std/collections/struct.VecDeque.html"),
        LIB("String / &amp;str", "Text. format!(\"x = {}\", x) builds strings; text() takes &amp;str.", "https://doc.rust-lang.org/std/string/struct.String.html"),
        LIB("Iterators", "for x in list.iter(), .map(), .filter(), .sum(), .enumerate().", "https://doc.rust-lang.org/std/iter/trait.Iterator.html"),
        LIB("f32 math", "angle.sin(), x.sqrt(), y.atan2(x), v.abs(): math is a method on the number.", "https://doc.rust-lang.org/std/primitive.f32.html"),
        LIB("println! / format!", "Print to the console, build text. Processing's println() works too.", "https://doc.rust-lang.org/std/macro.println.html"),
    ]) + "\n </div>\n\n <h2>Processing's types</h2>\n <div class=\"lib-grid\">\n " + "\n ".join([
        LIB("PVector", "2D and 3D vectors: v.add(&amp;w), v.mag(), v.normalize(), and + - * / between vectors.", "/reference/PVector.html"),
        LIB("Color", "A color: color_rgb(255, 0, 0), red(c), lerp_color(a, b, t). Color::from_u32 for pixels."),
        LIB("IntList / FloatList / StringList", "Processing's lists, with sort(), shuffle(), sum() and the rest."),
        LIB("IntDict / FloatDict / StringDict", "Processing's dictionaries."),
        LIB("Table / TableRow", "CSV and TSV files: load_table(), t.get_row_count(), row.get_float(\"x\")."),
        LIB("Json / Xml", "load_json_object(), json.get_json_array(\"items\"), load_xml(), xml.get_children(\"item\")."),
        LIB("Images and layers", "Images are ids (u64): img.width(), img.get(x, y), img.load_pixels(). Layers from create_graphics() draw between begin_graphics(pg) and end_graphics()."),
        LIB("PShape / fonts / PShader", "SVG and OBJ shapes, create_shape(), fonts from create_font(), and GLSL shaders."),
    ]) + "\n </div>\n </div>",
}


def card(tag, title, body):
    return f"""      <div class="wn-card">
        <div class="wn-tag {tag.lower()}">{tag}</div>
        <div class="wn-card-title">{title}</div>
        <div class="wn-card-body">
{body}
        </div>
      </div>"""


WHATS_NEW = {
    "lua": """<div class="content">
    <h1>What's New</h1>
    <p class="prelude">
      Lua Mode keeps Processing's names. <strong>The API is the one you know:</strong>
      <code>setup()</code>, <code>draw()</code>, <code>ellipse()</code>, <code>background()</code>,
      <code>mouseX</code>, <code>mouseY</code>, <code>fill()</code>, <code>stroke()</code> all work the same way.
      What changes is the language around them. These are the things to know.
    </p>
    <div class="wn-grid">
""" + "\n".join([
        card("Changed", "Functions end with end", """          <p>Blocks use <code>then</code>, <code>do</code> and <code>end</code> instead of braces, and lines don't need semicolons.</p>
          <pre>function draw()
  if mouseX > width / 2 then
    fill(255)
  else
    fill(0)
  end
end</pre>"""),
        card("Changed", "Variables are local or global", """          <p>There are no types to write. <code>local x = 10</code> makes a variable for the file or the function it's in. Variables a sketch keeps between frames go at the top of the file.</p>"""),
        card("Changed", "Text joins with ..", """          <p><code>+</code> only adds numbers. Join text with <code>..</code>: <code>text("score: " .. score, 10, 20)</code>.</p>"""),
        card("Changed", "Lists are tables, counted from 1", """          <p>A Java array is a table: <code>local xs = {1, 2, 3}</code>, and <code>xs[1]</code> is the first one. <code>#xs</code> is how many there are. <code>table.insert(xs, v)</code> adds to the end, and <code>for i, v in ipairs(xs) do ... end</code> goes through them.</p>
          <p>Processing's own indexes stay as they are in Java: <code>pixels[]</code>, <code>get(i)</code> on IntList and the like are counted from 0, so the index math from Java examples still works.</p>"""),
        card("Changed", "Methods use a colon", """          <p>Calling a method on an object uses <code>:</code>, as in <code>v:add(w)</code>, <code>img:get(x, y)</code> or <code>pg:beginDraw()</code>. Fields are still read with a dot: <code>img.width</code>, <code>v.x</code>.</p>"""),
        card("Changed", "Classes are tables with new()", """          <p>Lua has no <code>class</code> keyword. A class is a table with a <code>new</code> function, and its methods are written with a colon:</p>
          <pre>Ball = {}
Ball.__index = Ball

function Ball.new(x, y)
  local self = setmetatable({}, Ball)
  self.x, self.y = x, y
  return self
end

function Ball:display()
  ellipse(self.x, self.y, 20, 20)
end</pre>"""),
        card("Changed", "Division doesn't round", """          <p><code>7 / 2</code> is <code>3.5</code>. When you want Java's whole-number division, use <code>7 // 2</code>, or <code>int()</code>.</p>"""),
        card("Same", "mousePressed works both ways", """          <p>As in Java, <code>mousePressed</code> is true while the mouse is held, and <code>function mousePressed()</code> runs once per click. The same goes for <code>keyPressed</code>.</p>"""),
        card("New", "Two renderers", """          <p>The toolbar has a renderer menu. The default draws on the CPU. <strong>libprocessing</strong> draws with Bevy and wgpu on your graphics card, with real 3D lights and shaders.</p>"""),
    ]) + "\n    </div>\n  </div>",
    "rust": """<div class="content">
    <h1>What's New</h1>
    <p class="prelude">
      Rust Mode keeps Processing's shape. <strong>A sketch is still setup(), draw() and the calls you know.</strong>
      What changes is that it's Rust, so types are strict and names use snake_case:
      <code>noStroke()</code> is <code>no_stroke()</code> and <code>mouseX</code> is <code>mouse_x()</code>
      (the camelCase names work too). These are the things to know.
    </p>
    <div class="wn-grid">
""" + "\n".join([
        card("Changed", "Sketch variables are let at the top", """          <p>Variables your sketch keeps between frames are <code>let</code> lines at the top of the file. Add <code>mut</code> when they change. Rust Mode makes them available in <code>setup()</code>, <code>draw()</code> and the event functions.</p>
          <pre>let mut x: f32 = 0.0;

fn draw() {
    background(0);
    x += 1.0;
    ellipse(x, 50.0, 20.0, 20.0);
}</pre>"""),
        card("Changed", "Numbers have one type", """          <p>Rust doesn't mix <code>i32</code> and <code>f32</code> on its own. Write <code>2.0</code> when the number is an f32, and convert with <code>as</code>: <code>i as f32</code>, <code>x as i32</code>. Processing's calls take whole numbers fine: <code>size(640, 360)</code>, <code>fill(255, 0, 0)</code>.</p>"""),
        card("Changed", "Math is a method", """          <p><code>sin(a)</code> becomes <code>a.sin()</code>, <code>sqrt(x)</code> can be <code>x.sqrt()</code>, and <code>atan2(y, x)</code> is <code>y.atan2(x)</code>. <code>map()</code>, <code>dist()</code>, <code>lerp()</code>, <code>constrain()</code> and <code>random()</code> are the same as in Java.</p>"""),
        card("Changed", "Classes are structs", """          <p>A class becomes a <code>struct</code> with its fields, and an <code>impl</code> with <code>new()</code> and its methods. A method that changes the object takes <code>&amp;mut self</code>.</p>
          <pre>struct Ball { x: f32, y: f32 }

impl Ball {
    fn new(x: f32, y: f32) -> Ball {
        Ball { x, y }
    }
    fn display(&amp;self) {
        ellipse(self.x, self.y, 20.0, 20.0);
    }
}</pre>
          <p>Rust has no <code>extends</code>. A struct can hold the one it builds on as a field, and a <code>trait</code> lets different kinds share one list.</p>"""),
        card("Changed", "Lists are Vec", """          <p>Java's arrays and ArrayList are both <code>Vec</code>: <code>vec![0.0; 10]</code>, <code>list.push(v)</code>, <code>list.len()</code>, <code>for b in balls.iter_mut() { ... }</code>.</p>"""),
        card("Changed", "Text uses format!", """          <p>Join text with <code>format!</code>: <code>text(&amp;format!("score: {}", score), 10.0, 20.0)</code>. Functions that take text take <code>&amp;str</code>.</p>"""),
        card("Changed", "Images and layers are ids", """          <p><code>load_image()</code> and <code>create_graphics()</code> give you a <code>u64</code> id. Ask it for what you need: <code>img.width()</code>, <code>img.get(x, y)</code>. Draw into a layer between <code>begin_graphics(pg)</code> and <code>end_graphics()</code>.</p>
          <p>Pixels are a copy: <code>let mut px = load_pixels();</code>, change it, then <code>update_pixels(&amp;px);</code>.</p>"""),
        card("Same", "Overloads by number of arguments", """          <p><code>fill(255)</code>, <code>fill(255, 0, 0)</code> and <code>fill(255, 0, 0, 128)</code> all work. Rust Mode picks the right engine function for you (<code>fill_rgb</code>, <code>fill_rgba</code>...).</p>"""),
        card("New", "Two renderers", """          <p>The toolbar has a renderer menu. The default draws on the CPU. <strong>libprocessing</strong> draws with Bevy and wgpu on your graphics card, with real 3D lights and shaders.</p>"""),
    ]) + "\n    </div>\n  </div>",
}

CONTENT = {k: {"tutorials/index.html": TUTORIALS[k], "downloads/index.html": DOWNLOADS[k],
               "libraries/index.html": LIBRARIES[k], "whats-new/index.html": WHATS_NEW[k]} for k in ("lua", "rust")}

ENGINE = {"lua": "a small native runner (the same drawing engine as Rust Mode)",
          "rust": "Rust's compiler against a prebuilt engine"}

TEXT = {
    k: [
        (CPP_FIRST, FIRST[k]),
        ("C++ Mode runs inside the Processing IDE. Install Processing itself first, then come back here.",
         f"C++ Mode runs inside the Processing IDE. Install Processing itself first, then come back here."),
        ("Open Processing, click the mode dropdown in the top-right of the editor, choose <strong>Add Mode...</strong>, then search for <strong>C++ Mode</strong> in the Contribution Manager and click Install.",
         install_steps(k).replace("<ol class=\"step-list\">", "<ol>")),
        ('Full walkthrough with screenshots: see <a href="/downloads#cpp-mode" style="border-bottom:1px solid #ddd;">Looking for the C++ Mode?</a> on the Downloads page.',
         f'More about installing: see <a href="/downloads#{k}-mode" style="border-bottom:1px solid #ddd;">Installing C++ Mode</a> on the Downloads page.'),
        ("That's a complete sketch. Under the hood it's compiling to real C++ and running natively, but everything about writing it looks and feels like any other Processing mode.",
         "That's a complete sketch. " + ("It runs on a native runner, so it starts right away, and everything about writing it looks and feels like any other Processing mode."
                                          if k == "lua" else "Under the hood it's compiled to a native program, but everything about writing it looks and feels like any other Processing mode.")),
        ('<a href="/downloads">Using your own editor instead? →</a>',
         '<a href="/whats-new">Coming from Java? →</a>' if k == "lua" else '<a href="/downloads#crate">Using your own editor instead? →</a>'),
        ("built-in <code>mouseX</code> and <code>mouseY</code> variables",
         "built-in <code>mouseX</code> and <code>mouseY</code> variables" if k == "lua"
         else "mouse position from <code>mouse_x()</code> and <code>mouse_y()</code> (Processing's <code>mouseX</code> and <code>mouseY</code>)"),
        # home page
        ("Using your own editor and build system? Drop the engine into your project as a plug-and-play folder or a CMake target.",
         "Want the code? Lua Mode is open source, and every release is on GitHub." if k == "lua"
         else "Using your own editor? The engine is a Rust crate you can add to any Cargo project."),
        ("Download the headers", "Get the source" if k == "lua" else "Use the crate"),
        ("Install C++ Mode straight from the Processing IDE's Contribution Manager. No separate download needed.",
         "Download one zip, unzip it into your sketchbook's modes folder, and restart Processing."),
        # about
        ("The window, the event loop, the OpenGL context, all of it is taken care of.",
         "The window, the event loop, the drawing engine, all of it is taken care of."),
        ('<a href="https://github.com/processing-cpp/processing.cpp" style="border-bottom:1px solid #ddd;">GitHub</a>',
         f'<a href="{REPO[k]}" style="border-bottom:1px solid #ddd;">GitHub</a>'),
    ] for k in ("lua", "rust")
}

# The C++ site's copy for these has no Lua or Rust version
DROP = {k: ["downloads/cmake-setup.html", "downloads/plugandplay-setup.html", "editor", "error"] for k in ("lua", "rust")}
