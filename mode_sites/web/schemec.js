// wscheme's compile step: Scheme Mode sketch -> JavaScript, with the same
// compiler the browser has (scheme-web.js), so errors come back before the
// sketch runs. Reads the sketch on stdin; prints {"js": ...} or {"error": ...}.
const path = require('path');
const dir = path.resolve(process.argv[2] || __dirname);
globalThis.window = globalThis;
require(path.join(dir, 'scheme-web.js'));
// the runtime's names (scheme-builtins.json, recorded from the browser's runtime):
// the compiler only needs to know which names are built in
const names = JSON.parse(require('fs').readFileSync(path.join(dir, 'scheme-builtins.json'), 'utf8'));
let src = '';
process.stdin.on('data', (d) => (src += d));
process.stdin.on('end', () => {
  try {
    const js = globalThis.SchemeWeb.compile(src, names);
    process.stdout.write(JSON.stringify({ js }));
  } catch (e) {
    const ln = e.schemeLine || e.line;
    process.stdout.write(JSON.stringify({ error: (ln ? 'line ' + ln + ': ' : '') + (e.message || String(e)) }));
  }
});
