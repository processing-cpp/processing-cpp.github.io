# Translating the examples

`tolua.py` and `tors.py` turn a Processing (Java) example into a Lua Mode or
Rust Mode sketch. They give a first draft: each one was then run (Lua) or
compiled and run (Rust) against the real mode, and the few that needed it
were fixed by hand in `fix_lua.py`, `fix_rs.py` and `rs_hand/`.

    python3 tolua.py Bounce.pde > bounce.lua
    python3 tors.py Bounce.pde > bounce.rs

Needs `pip install tree-sitter tree-sitter-java`. `rsig.json` and
`rover.json` are RustMode's function signatures and overloads; refresh them
when the engine's API changes.

The results live in each site's `content/examples/`, and
`clone_mode_sites.py` builds the example pages from them.
