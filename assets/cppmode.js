// CppMode CodeMirror mode
// Keywords loaded from cppmode-keywords.js (auto-generated from keywords.txt)
// Colors from Processing 4 theme.txt:
//   function1/function2 = #006698 plain
//   function4           = #006698 bold
//   keyword1/keyword2/keyword6 = #30987F plain
//   keyword3            = #6D9810 plain
//   keyword4            = #DB4D7A plain
//   keyword5            = #E7671C plain
//   literal1            = #738A63 plain
//   literal2            = #754891 plain

(function(mod) {
  if (typeof exports == "object" && typeof module == "object") mod(require("codemirror"));
  else if (typeof define == "function" && define.amd) define(["codemirror"], mod);
  else mod(CodeMirror);
})(function(CodeMirror) {
"use strict";

// C++ language keywords (from CppLexer.java)
const CPP_KEYWORDS = new Set([
  "alignas","alignof","and","and_eq","asm","auto","bitand","bitor",
  "bool","break","case","catch","char","char16_t","char32_t","class",
  "compl","concept","const","consteval","constexpr","constinit","const_cast",
  "continue","co_await","co_return","co_yield","decltype","default","delete",
  "do","double","dynamic_cast","else","enum","explicit","export","extern",
  "false","float","for","friend","goto","if","inline","int","long","mutable",
  "namespace","new","noexcept","not","not_eq","nullptr","operator","or","or_eq",
  "private","protected","public","register","reinterpret_cast","requires",
  "return","short","signed","sizeof","static","static_assert","static_cast",
  "struct","switch","template","this","thread_local","throw","true","try",
  "typedef","typeid","typename","union","unsigned","using","virtual","void",
  "volatile","wchar_t","while","xor","xor_eq","override","final",
]);

const CTRL_FLOW = new Set([
  "if","else","for","while","do","switch","case","break",
  "continue","default","return","try","catch","throw","goto",
]);
const LANG_KW = new Set([
  "void","class","struct","enum","namespace","template","typename",
  "public","private","protected","static","const","constexpr","consteval",
  "new","delete","this","inline","virtual","override","explicit","final",
  "using","typedef","extern","auto","friend","mutable","volatile","register",
  "sizeof","decltype","noexcept","operator","alignas","alignof",
]);
const TYPE_KW = new Set([
  "int","float","double","bool","char","long","short","unsigned",
  "signed","wchar_t","char16_t","char32_t",
]);

function kw() { return window.CPPMODE_KEYWORDS || {}; }
function inCat(cat, w) { const s = kw()[cat]; return s && s.has(w); }

// Map keywords.txt categories to CodeMirror token names
// which map to CSS classes .cm-s-cppmode .cm-<name>
function classifyIdent(w, stream) {
  // Peek ahead on the current line to see if '(' follows (ignoring spaces/tabs)
  const hasParen = stream ? /^[ \t]*\(/.test(stream.string.slice(stream.pos)) : false;
  // Words that appear in BOTH a function category AND keyword5 are paren-sensitive:
  // if '(' follows -> function color; otherwise -> keyword5 (type) color.
  const inFunc = inCat('FUNCTION4', w) || inCat('FUNCTION1', w) ||
                 inCat('FUNCTION2', w) || inCat('FUNCTION3', w);
  const inType = inCat('KEYWORD5', w);
  if (inFunc && inType) {
    // Dual-role word: color as function only if paren follows
    if (hasParen) {
      if (inCat('FUNCTION4', w)) return 'function4';
      return 'function2';
    }
    return 'keyword5';
  }
  // Single-role words: check all categories in priority order
  if (inCat('FUNCTION4', w)) return hasParen ? 'function4' : null;  // functions need parens
  if (inCat('FUNCTION2', w)) return hasParen ? 'function2' : null;
  if (inCat('FUNCTION1', w)) return hasParen ? 'function2' : null;
  if (inCat('FUNCTION3', w)) return hasParen ? 'function2' : null;
  if (inCat('LITERAL2',  w)) return 'literal2';   // #754891
  if (inCat('LITERAL1',  w)) return 'literal1';   // #738A63
  if (inCat('KEYWORD4',  w)) return 'keyword4';   // #DB4D7A
  if (inCat('KEYWORD5',  w)) return 'keyword5';   // #E7671C
  if (inCat('KEYWORD3',  w)) return 'keyword3';   // #6D9810
  if (inCat('KEYWORD6',  w)) return 'keyword6';   // #30987F
  if (inCat('KEYWORD1',  w)) return 'keyword1';   // #30987F
  if (inCat('KEYWORD2',  w)) return 'keyword2';   // #30987F
  return null;
}

CodeMirror.defineMode("cppmode", function() {
  return {
    startState() { return { inBlockComment: false }; },

    token(stream, state) {
      if (state.inBlockComment) {
        if (stream.match("*/")) state.inBlockComment = false;
        else stream.next();
        return "comment";
      }

      if (stream.eatSpace()) return null;

      // Preprocessor
      if (stream.sol() && stream.peek() === '#') {
        while (!stream.eol()) {
          if (stream.peek() === '\\') { stream.next(); stream.next(); }
          else stream.next();
        }
        return "preprocessor";
      }

      // Line comment
      if (stream.match("//")) { stream.skipToEnd(); return "comment"; }

      // Block comment
      if (stream.match("/*")) {
        state.inBlockComment = true;
        while (!stream.eol()) {
          if (stream.match("*/")) { state.inBlockComment = false; break; }
          stream.next();
        }
        return "comment";
      }

      // String literal
      if (stream.peek() === '"') {
        stream.next();
        while (!stream.eol()) {
          const ch = stream.next();
          if (ch === '\\') stream.next();
          else if (ch === '"') break;
        }
        return "string";
      }

      // Char literal
      if (stream.peek() === "'") {
        stream.next();
        while (!stream.eol()) {
          const ch = stream.next();
          if (ch === '\\') stream.next();
          else if (ch === "'") break;
        }
        return "string-2";
      }

      // Numbers
      if (stream.match(/^0[xX][0-9a-fA-F]+[uUlL]*/)) return "number";
      if (stream.match(/^\d+\.?\d*(?:[eE][+-]?\d+)?[fFuUlL]*/)) return "number";
      if (stream.match(/^\.\d+(?:[eE][+-]?\d+)?[fF]?/)) return "number";

      // Identifiers and keywords
      if (stream.match(/^[a-zA-Z_]\w*/)) {
        const w = stream.current();

        // C++ language keywords take priority
        if (CPP_KEYWORDS.has(w)) {
          if (w === "true" || w === "false" || w === "nullptr") return "keyword1";
          if (CTRL_FLOW.has(w)) return "keyword3";
          if (LANG_KW.has(w))   return "keyword6";
          if (TYPE_KW.has(w))   return "keyword5";
          return "keyword6";
        }

        // Then check keywords.txt categories
        const cls = classifyIdent(w, stream);
        if (cls) return cls;

        return "variable";
      }

      stream.next();
      return "operator";
    }
  };
});

CodeMirror.defineMIME("text/x-cppmode", "cppmode");
});
