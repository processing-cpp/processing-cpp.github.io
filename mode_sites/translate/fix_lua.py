"""Hand fixes on top of the translator output, by example."""
FIX = {
 "datatype-conversion": [
  ('f = float(c)  -- Sets f = 65.0', 'f = string.byte(c) + 0.0  -- Sets f = 65.0 (a letter is text in Lua, string.byte gives its code)'),
  ('b = byte(c / 2)  -- Sets b to 32', 'b = byte(string.byte(c) // 2)  -- Sets b to 32'),
 ],
 "multiple-constructors": [
  ('''-- First version of the Spot constructor;
-- the fields are assigned default values
function Spot.new()
  local self = setmetatable({}, Spot)
  self.radius = 40
  self.x = width * 0.25
  self.y = height * 0.5
  return self
end

-- Second version of the Spot constructor;
-- the fields are assigned with parameters
function Spot.new(xpos, ypos, r)''', '''-- Lua has one function per name, so both versions of the constructor
-- live in Spot.new. With no arguments the fields get default values;
-- with three they are assigned from the parameters.
function Spot.new(xpos, ypos, r)
  if xpos == nil then
    local self = setmetatable({}, Spot)
    self.radius = 40
    self.x = width * 0.25
    self.y = height * 0.5
    return self
  end'''),
 ],
 "penrose-snowflake": [
  ('''    elseif (step >= 48) and (step <= 57) then
      repeats = repeats + (step - 48)''', '''    elseif step >= "0" and step <= "9" then
      repeats = repeats + tonumber(step)'''),
 ],
 "penrose-tile": [
  ('''    elseif (step >= 48) and (step <= 57) then
      repeats = int(step) - 48''', '''    elseif step >= "0" and step <= "9" then
      repeats = tonumber(step)'''),
 ],
}

def apply(slug, src):
    for a, b in FIX.get(slug, []):
        assert a in src, (slug, a[:60])
        src = src.replace(a, b)
    return src
