"""Hand fixes on top of the Rust translator output, by example. Each entry is
a list of (old, new) replacements, or a whole file in rs_hand/<name>.rs."""
import os

HAND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rs_hand")

FIX = {
 "multiple-constructors": [
  ("    sp2 = Spot::new(width() * 0.5, height() * 0.5, 120.0);",
   "    sp2 = Spot::with(width() * 0.5, height() * 0.5, 120.0);"),
  ("""    // Second version of the Spot constructor;
    // the fields are assigned with parameters
    fn new(xpos: f32, ypos: f32, r: f32) -> Spot {""",
   """    // Second version of the Spot constructor;
    // the fields are assigned with parameters.
    // Rust has no overloading, so this one gets its own name.
    fn with(xpos: f32, ypos: f32, r: f32) -> Spot {"""),
 ],
 "circle-collision": [
  ("    balls[0].check_collision(&mut balls[1]);",
   "    // two balls of the same list, one changed through the other\n"
   "    let (first, rest) = balls.split_at_mut(1);\n"
   "    first[0].check_collision(&mut rest[0]);"),
 ],
 "penrose-snowflake": [
  ("} else if (step >= 48) && (step <= 57) {\n                repeats += (step as i32) - 48;",
   "} else if step.is_ascii_digit() {\n                repeats += step.to_digit(10).unwrap() as i32;"),
 ],
 "penrose-tile": [
  ("} else if (step >= 48) && (step <= 57) {\n                repeats = step as i32 - 48;",
   "} else if step.is_ascii_digit() {\n                repeats = step.to_digit(10).unwrap() as i32;"),
 ],
 "loading-json-data": [
  ('position.set_int("x", mouse_x());', 'position.set_int("x", mouse_x() as i32);'),
  ('position.set_int("y", mouse_y());', 'position.set_int("y", mouse_y() as i32);'),
  ('    let mut bubbleData = json.get_json_array("bubbles");\n    bubbleData.append',
   '    // get_mut: the array inside json, to change it in place\n    let bubbleData = json.get_mut("bubbles");\n    bubbleData.append'),
 ],
}


def apply(slug, src):
    hand = os.path.join(HAND, slug + ".rs")
    if os.path.exists(hand):
        return open(hand).read()
    for a, b in FIX.get(slug, []):
        assert a in src, (slug, a[:70])
        src = src.replace(a, b)
    return src
