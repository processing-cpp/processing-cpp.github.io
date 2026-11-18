"""Shared bits for the Java -> Lua / Rust example translators: parsing,
comments, a small type table, and Processing's builtin return types."""
import re
from jparse import parse

INT_BUILTINS = {"width", "height", "mouseX", "mouseY", "pmouseX", "pmouseY", "frameCount",
                "keyCode", "displayWidth", "displayHeight", "pixelWidth", "pixelHeight"}
FLOAT_BUILTINS = {"frameRate"}
RET = {  # builtin function -> return type
    "millis": "int", "second": "int", "minute": "int", "hour": "int", "day": "int",
    "month": "int", "year": "int", "__int": "int", "round": "int", "floor": "int",
    "ceil": "int", "random": "float", "noise": "float", "sin": "float", "cos": "float",
    "tan": "float", "atan2": "float", "atan": "float", "asin": "float", "acos": "float",
    "sqrt": "float", "pow": "float", "map": "float", "lerp": "float", "dist": "float",
    "mag": "float", "norm": "float", "radians": "float", "degrees": "float", "exp": "float",
    "log": "float", "randomGaussian": "float", "__float": "float", "sq": "float",
    "color": "color", "lerpColor": "color", "get": "color", "red": "float", "green": "float",
    "blue": "float", "alpha": "float", "hue": "float", "saturation": "float",
    "brightness": "float", "str": "String", "__str": "String", "nf": "String",
    "nfc": "String", "nfs": "String", "nfp": "String", "hex": "String", "binary": "String",
    "__char": "char", "textWidth": "float", "loadImage": "PImage", "createImage": "PImage",
    "createGraphics": "PGraphics", "loadShape": "PShape", "createShape": "PShape",
    "loadStrings": "String[]", "split": "String[]", "splitTokens": "String[]",
    "createFont": "PFont", "loadFont": "PFont", "loadTable": "Table",
    "loadJSONObject": "JSONObject", "loadJSONArray": "JSONArray", "loadXML": "XML",
    "requestImage": "PImage", "trim": "String", "join": "String", "unhex": "int",
    "unbinary": "int", "createVector": "PVector", "abs": None, "min": None, "max": None,
    "constrain": None,
}


def text(b, n):
    return b[n.start_byte:n.end_byte].decode()


def named(n):
    return [c for c in n.children if c.is_named]


def is_comment(n):
    return n.type in ("line_comment", "block_comment")


def base_type(t):
    """'float[][]' -> 'float', 'ArrayList<Ball>' -> 'ArrayList'"""
    return re.sub(r"<.*>|\[\]", "", t or "")


def elem_type(t):
    if not t:
        return None
    if t.endswith("[]"):
        return t[:-2]
    m = re.match(r"\w+<\s*(.+?)\s*>$", t)
    if m:
        return m.group(1)
    if t == "IntList":
        return "int"
    if t == "FloatList":
        return "float"
    if t == "StringList":
        return "String"
    return None


def numeric(t):
    return t in ("int", "float", "double", "long", "byte", "short", "char", "color")


def intlike(t):
    return t in ("int", "long", "byte", "short", "char")


class Scope:
    def __init__(self):
        self.stack = [{}]

    def push(self):
        self.stack.append({})

    def pop(self):
        self.stack.pop()

    def add(self, name, t):
        self.stack[-1][name] = t

    def get(self, name):
        for d in reversed(self.stack):
            if name in d:
                return d[name]
        return None

    def local(self, name):
        """declared in a function scope (not the sketch level)"""
        for d in reversed(self.stack[1:]):
            if name in d:
                return True
        return False


def type_text(b, n):
    """Type of a declaration node (local_variable_declaration, field, param) with
    array dims on the declarator folded in."""
    t = n.child_by_field_name("type")
    return re.sub(r"\s+", "", text(b, t)) if t else None


class ClassInfo:
    def __init__(self, name, node):
        self.name = name
        self.node = node
        self.base = None
        self.fields = {}
        self.methods = {}
        self.ctors = []
