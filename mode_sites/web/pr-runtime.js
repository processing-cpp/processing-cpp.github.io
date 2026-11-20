// Runs a sketch built for the browser: a wasm32-wasip1 program with the
// engine's pr_* exports (RustMode's engine with its "wasm" feature: Rust
// sketches, and Lua Mode's runner). A small WASI layer gives it the clock,
// random numbers, printing and files (the sketch's own files live in memory);
// the page drives the frames and the input and copies the pixels to a canvas.
//
//   PRRuntime.start({ wasm, canvas, files, args, env, print, printErr, onRunning, onError })
(function () {
  'use strict';

  const ESUCCESS = 0, EBADF = 8, EINVAL = 28, ENOENT = 44, ENOSYS = 52, ENOTDIR = 54, EEXIST = 20;
  const enc = new TextEncoder(), dec = new TextDecoder();

  class Exit { constructor(code) { this.code = code; } }

  function start(opts) {
    const files = new Map();                       // path -> Uint8Array
    for (const [k, v] of Object.entries(opts.files || {})) files.set(norm(k), typeof v === 'string' ? enc.encode(v) : new Uint8Array(v));
    const args = ['sketch'].concat(opts.args || []);
    const env = Object.entries(opts.env || {}).map(([k, v]) => k + '=' + v);
    const print = opts.print || console.log, printErr = opts.printErr || console.warn;
    const canvas = opts.canvas, ctx2d = canvas.getContext('2d');
    let inst = null, mem = null, ex = null, stopped = false, errText = '';
    const t0 = performance.now();

    // open files: fd -> { path, data, pos, dir, write }
    const fds = new Map();
    fds.set(3, { dir: true, path: '' });           // the preopened sketch folder "/"
    let nextFd = 4;

    function norm(p) { return String(p).replace(/^\.?\/+/, '').replace(/\/+/g, '/'); }
    function u8() { return new Uint8Array(mem.buffer); }
    function dv() { return new DataView(mem.buffer); }
    function str(ptr, len) { return dec.decode(u8().subarray(ptr, ptr + len)); }
    function lines(buf, sink) {
      buf.text += dec.decode(buf.bytes, { stream: true }); buf.bytes = null;
      let i;
      while ((i = buf.text.indexOf('\n')) >= 0) { sink(buf.text.slice(0, i)); buf.text = buf.text.slice(i + 1); }
    }
    const outBuf = { text: '' }, errBuf = { text: '' };
    function flush() {
      if (outBuf.text) { print(outBuf.text); outBuf.text = ''; }
      if (errBuf.text) { printErr(errBuf.text); errBuf.text = ''; }
    }
    function iovs(ptr, n, fn) {
      const d = dv(); let total = 0;
      for (let i = 0; i < n; i++) {
        const p = d.getUint32(ptr + i * 8, true), l = d.getUint32(ptr + i * 8 + 4, true);
        const done = fn(p, l); total += done;
        if (done < l) break;
      }
      return total;
    }
    function strList(list, ptrs, buf) {
      const d = dv(), m = u8();
      for (const s of list) {
        const b = enc.encode(s + '\0');
        d.setUint32(ptrs, buf, true); ptrs += 4;
        m.set(b, buf); buf += b.length;
      }
      return ESUCCESS;
    }
    function sizes(list, cPtr, sPtr) {
      dv().setUint32(cPtr, list.length, true);
      dv().setUint32(sPtr, list.reduce((n, s) => n + enc.encode(s).length + 1, 0), true);
      return ESUCCESS;
    }
    function isDir(path) {
      if (path === '') return true;
      const pre = path + '/';
      for (const k of files.keys()) if (k.startsWith(pre)) return true;
      return false;
    }
    function filestat(ptr, size, dir) {
      const d = dv();
      for (let i = 0; i < 64; i += 8) d.setBigUint64(ptr + i, 0n, true);
      d.setUint8(ptr + 16, dir ? 3 : 4);
      d.setBigUint64(ptr + 24, 1n, true);
      d.setBigUint64(ptr + 32, BigInt(size), true);
    }

    const wasi = {
      args_get: (a, b) => strList(args, a, b),
      args_sizes_get: (c, s) => sizes(args, c, s),
      environ_get: (a, b) => strList(env, a, b),
      environ_sizes_get: (c, s) => sizes(env, c, s),
      clock_res_get: (id, ptr) => { dv().setBigUint64(ptr, 1000n, true); return ESUCCESS; },
      clock_time_get: (id, prec, ptr) => {
        const ns = id === 0 ? BigInt(Date.now()) * 1000000n : BigInt(Math.round((performance.now() - t0) * 1e6));
        dv().setBigUint64(ptr, ns, true); return ESUCCESS;
      },
      random_get: (ptr, len) => {
        const m = u8();
        for (let i = 0; i < len; i += 65536) crypto.getRandomValues(m.subarray(ptr + i, ptr + Math.min(len, i + 65536)));
        return ESUCCESS;
      },
      fd_write: (fd, ptr, n, out) => {
        let total;
        if (fd === 1 || fd === 2) {
          const buf = fd === 1 ? outBuf : errBuf;
          total = iovs(ptr, n, (p, l) => { buf.bytes = u8().slice(p, p + l); lines(buf, fd === 1 ? print : (t) => { errText += t + '\n'; printErr(t); }); return l; });
        } else {
          const f = fds.get(fd);
          if (!f || f.dir) return EBADF;
          total = iovs(ptr, n, (p, l) => {
            const add = u8().slice(p, p + l);
            const end = f.pos + l;
            if (end > f.data.length) { const g = new Uint8Array(Math.max(end, f.data.length * 2)); g.set(f.data); f.data = g; f.len = f.len || 0; }
            f.data.set(add, f.pos); f.pos = end; f.len = Math.max(f.len || 0, end);
            return l;
          });
        }
        dv().setUint32(out, total, true); return ESUCCESS;
      },
      fd_read: (fd, ptr, n, out) => {
        if (fd === 0) { dv().setUint32(out, 0, true); return ESUCCESS; }
        const f = fds.get(fd);
        if (!f || f.dir) return EBADF;
        const total = iovs(ptr, n, (p, l) => {
          const len = f.len !== undefined ? f.len : f.data.length;
          const k = Math.max(0, Math.min(l, len - f.pos));
          u8().set(f.data.subarray(f.pos, f.pos + k), p); f.pos += k; return k;
        });
        dv().setUint32(out, total, true); return ESUCCESS;
      },
      fd_pread: () => ENOSYS, fd_pwrite: () => ENOSYS,
      fd_seek: (fd, off, whence, out) => {
        const f = fds.get(fd);
        if (!f || f.dir) return EBADF;
        const len = f.len !== undefined ? f.len : f.data.length;
        const base = whence === 0 ? 0 : whence === 1 ? f.pos : len;
        const p = base + Number(off);
        if (p < 0) return EINVAL;
        f.pos = p; dv().setBigUint64(out, BigInt(p), true); return ESUCCESS;
      },
      fd_tell: (fd, out) => { const f = fds.get(fd); if (!f) return EBADF; dv().setBigUint64(out, BigInt(f.pos || 0), true); return ESUCCESS; },
      fd_close: (fd) => {
        const f = fds.get(fd);
        if (!f) return EBADF;
        if (f.write) files.set(f.path, f.data.slice(0, f.len || 0));
        fds.delete(fd); return ESUCCESS;
      },
      fd_sync: () => ESUCCESS, fd_datasync: () => ESUCCESS, fd_advise: () => ESUCCESS, fd_allocate: () => ESUCCESS,
      fd_fdstat_get: (fd, ptr) => {
        const d = dv();
        if (fd > 2 && !fds.has(fd)) return EBADF;
        const dir = fd > 2 && fds.get(fd).dir;
        d.setUint8(ptr, fd <= 2 ? 2 : dir ? 3 : 4);
        d.setUint16(ptr + 2, 0, true);
        d.setBigUint64(ptr + 8, 0xffffffffffffffffn, true);
        d.setBigUint64(ptr + 16, 0xffffffffffffffffn, true);
        return ESUCCESS;
      },
      fd_fdstat_set_flags: () => ESUCCESS, fd_fdstat_set_rights: () => ESUCCESS,
      fd_filestat_get: (fd, ptr) => {
        const f = fds.get(fd);
        if (fd <= 2) { filestat(ptr, 0, false); return ESUCCESS; }
        if (!f) return EBADF;
        filestat(ptr, f.dir ? 0 : (f.len !== undefined ? f.len : f.data.length), f.dir); return ESUCCESS;
      },
      fd_filestat_set_size: () => ESUCCESS, fd_filestat_set_times: () => ESUCCESS,
      fd_prestat_get: (fd, ptr) => {
        if (fd !== 3) return EBADF;
        dv().setUint8(ptr, 0); dv().setUint32(ptr + 4, 1, true); return ESUCCESS;
      },
      fd_prestat_dir_name: (fd, ptr, len) => { if (fd !== 3) return EBADF; u8()[ptr] = 47; return ESUCCESS; },
      fd_readdir: (fd, buf, len, cookie, out) => { dv().setUint32(out, 0, true); return ESUCCESS; },
      fd_renumber: () => ENOSYS,
      path_open: (dirfd, lookup, pathPtr, pathLen, oflags, rightsBase, rightsInh, fdflags, out) => {
        const base = fds.get(dirfd);
        if (!base || !base.dir) return EBADF;
        const path = norm((base.path ? base.path + '/' : '') + str(pathPtr, pathLen));
        const creat = oflags & 1, directory = oflags & 2, excl = oflags & 4, trunc = oflags & 8;
        const writing = (rightsBase & 64n) !== 0n || creat || trunc;
        let entry;
        if (files.has(path)) {
          if (creat && excl) return EEXIST;
          if (directory) return ENOTDIR;
          const data = trunc ? new Uint8Array(0) : files.get(path);
          entry = { path, data: new Uint8Array(data), len: data.length, pos: (fdflags & 1) ? data.length : 0, write: writing };
        } else if (isDir(path)) {
          entry = { path, dir: true };
        } else if (creat) {
          entry = { path, data: new Uint8Array(64), len: 0, pos: 0, write: true };
          files.set(path, new Uint8Array(0));
        } else return ENOENT;
        const fd = nextFd++; fds.set(fd, entry);
        dv().setUint32(out, fd, true); return ESUCCESS;
      },
      path_filestat_get: (dirfd, flags, pathPtr, pathLen, ptr) => {
        const base = fds.get(dirfd);
        if (!base) return EBADF;
        const path = norm((base.path ? base.path + '/' : '') + str(pathPtr, pathLen));
        if (files.has(path)) { filestat(ptr, files.get(path).length, false); return ESUCCESS; }
        if (isDir(path)) { filestat(ptr, 0, true); return ESUCCESS; }
        return ENOENT;
      },
      path_filestat_set_times: () => ESUCCESS,
      path_create_directory: () => ESUCCESS,
      path_remove_directory: () => ESUCCESS,
      path_unlink_file: (dirfd, p, l) => { const base = fds.get(dirfd); files.delete(norm((base && base.path ? base.path + '/' : '') + str(p, l))); return ESUCCESS; },
      path_rename: () => ENOSYS, path_link: () => ENOSYS, path_symlink: () => ENOSYS, path_readlink: () => ENOSYS,
      poll_oneoff: (inp, out, n, nout) => { dv().setUint32(nout, 0, true); return ESUCCESS; },
      proc_exit: (code) => { throw new Exit(code); },
      proc_raise: () => ENOSYS,
      sched_yield: () => ESUCCESS,
      sock_accept: () => ENOSYS, sock_recv: () => ENOSYS, sock_send: () => ENOSYS, sock_shutdown: () => ENOSYS,
    };

    function fail(e) {
      if (stopped) return;
      stopped = true;
      flush();
      let msg;
      if (e instanceof Exit) msg = e.code === 0 ? null : 'The sketch stopped (exit code ' + e.code + ').';
      else msg = (errText.trim() || String(e && e.message || e));
      if (msg && opts.onError) opts.onError(msg);
    }
    // call an export; a trap (a panic, a Lua error that ends the sketch) stops it with what it printed
    function call(name, ...a) {
      if (stopped) return;
      try { return ex[name](...a); }
      catch (e) { fail(e); }
    }

    // ── input ────────────────────────────────────────────────────────────
    let mouseX = 0, mouseY = 0, pressed = 0, focused = 1;
    const KEYS = { ArrowUp: 38, ArrowDown: 40, ArrowLeft: 37, ArrowRight: 39, Shift: 16, Control: 17, Alt: 18,
                   Meta: 157, Enter: 10, Backspace: 8, Tab: 9, Escape: 27, Delete: 127, Home: 36, End: 35,
                   PageUp: 33, PageDown: 34, Insert: 155 };
    function sendInput() { call('pr_input', mouseX, mouseY, pressed, performance.now() - t0, focused); }
    function pos(e) {
      const r = canvas.getBoundingClientRect();
      mouseX = (e.clientX - r.left) * canvas.width / (r.width || 1);
      mouseY = (e.clientY - r.top) * canvas.height / (r.height || 1);
    }
    function on(target, type, fn) { target.addEventListener(type, fn); listeners.push([target, type, fn]); }
    const listeners = [];
    on(canvas, 'mousedown', e => { pos(e); pressed = 1; sendInput(); call('pr_event', 1, 0); after(); });
    on(window, 'mouseup', e => { if (!pressed) return; pos(e); pressed = 0; sendInput(); call('pr_event', 2, 0); after(); });
    on(window, 'mousemove', e => { pos(e); sendInput(); call('pr_event', pressed ? 4 : 3, 0); after(); });
    on(canvas, 'wheel', e => { e.preventDefault(); sendInput(); call('pr_event', 5, Math.sign(e.deltaY)); after(); });
    on(window, 'keydown', e => {
      const coded = KEYS[e.key];
      const ch = e.key.length === 1 ? e.key.codePointAt(0) : (e.key === 'Enter' ? 10 : e.key === 'Backspace' ? 8 : e.key === 'Tab' ? 9 : e.key === 'Escape' ? 27 : e.key === 'Delete' ? 127 : 0);
      const code = coded !== undefined ? coded : (e.key.length === 1 ? e.key.toUpperCase().codePointAt(0) : 0);
      if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', ' ', 'Tab', 'Backspace'].includes(e.key)) e.preventDefault();
      sendInput(); call('pr_key', code, ch, 1); call('pr_event', 6, 0);
      if (ch) call('pr_event', 8, 0);
      after();
    });
    on(window, 'keyup', e => {
      const coded = KEYS[e.key];
      const code = coded !== undefined ? coded : (e.key.length === 1 ? e.key.toUpperCase().codePointAt(0) : 0);
      const ch = e.key.length === 1 ? e.key.codePointAt(0) : 0;
      sendInput(); call('pr_key', code, ch, 0); call('pr_event', 7, 0); after();
    });
    on(window, 'focus', () => { focused = 1; });
    on(window, 'blur', () => { focused = 0; });

    // ── frames ──────────────────────────────────────────────────────────
    let img = null, lastFrame = -1e9, raf = 0;
    function blit() {
      const w = ex.pr_width(), h = ex.pr_height();
      if (!w || !h) return;
      if (canvas.width !== w || canvas.height !== h || !img) {
        canvas.width = w; canvas.height = h; img = ctx2d.createImageData(w, h);
        if (opts.onResize) opts.onResize(w, h);
      }
      const src = new Uint32Array(mem.buffer, ex.pr_pixels(), w * h);
      const dst = new Uint32Array(img.data.buffer);
      for (let i = 0; i < src.length; i++) {
        const p = src[i];   // 0xRRGGBB -> bytes R,G,B,A (little endian 0xAABBGGRR)
        dst[i] = 0xff000000 | ((p & 0xff) << 16) | (p & 0xff00) | ((p >>> 16) & 0xff);
      }
      ctx2d.putImageData(img, 0, 0);
    }
    function after() {
      if (stopped) return;
      flush();
      if (call('pr_exited')) fail(new Exit(0));
    }
    function frame(now) {
      if (stopped) return;
      raf = requestAnimationFrame(frame);
      const fps = call('pr_frame_rate') || 60;
      const looping = call('pr_looping');
      const redraw = call('pr_take_redraw');
      if (!looping && !redraw) return;
      if (looping && now - lastFrame < 1000 / fps - 2) return;
      lastFrame = now;
      sendInput();
      call('pr_frame');
      if (stopped) return;
      blit();
      after();
    }

    // ── start ───────────────────────────────────────────────────────────
    function started() {
      flush();
      if (stopped) return;
      // setup() ran inside main; the first frame shows what it drew
      blit();
      if (opts.onRunning) opts.onRunning();
      raf = requestAnimationFrame(frame);
    }
    let ready;
    if (opts.emscripten) {
      // Lua Mode's runner, built with emscripten (Lua needs its longjmp):
      // opts.emscripten is the factory its -sMODULARIZE script defines
      ready = opts.emscripten({
        wasmBinary: opts.wasm,
        // hand emscripten the module ourselves so it never tries to fetch the .wasm by name
        locateFile: f => f,
        instantiateWasm: (imports, done) => {
          WebAssembly.instantiate(opts.wasm, imports).then(r => done(r.instance, r.module), e => fail(e));
          return {};
        },
        arguments: args.slice(1),
        noExitRuntime: true,
        preRun: [m => { for (const [k, v] of files) { const d = k.split('/').slice(0, -1).join('/'); if (d) m.FS.mkdirTree(d); m.FS.writeFile(k, v); } }],
        print: t => print(t),
        printErr: t => { errText += t + '\n'; printErr(t); },
        onAbort: e => fail(e),
        quit: (code, e) => { if (code) fail(new Exit(code)); },
      }).then(m => {
        mem = { get buffer() { return m.HEAPU8.buffer; } };
        ex = {};
        for (const n of ['pr_input', 'pr_key', 'pr_frame', 'pr_event', 'pr_pixels', 'pr_width', 'pr_height', 'pr_looping',
                         'pr_take_redraw', 'pr_frame_rate', 'pr_exited']) ex[n] = m['_' + n];
        started();
      }, e => fail(e));
    } else {
      ready = WebAssembly.instantiate(opts.wasm, { wasi_snapshot_preview1: wasi, wasi_unstable: wasi }).then(r => {
        inst = r.instance; mem = inst.exports.memory; ex = inst.exports;
        try {
          if (inst.exports._start) inst.exports._start();
          else if (inst.exports._initialize) inst.exports._initialize();
        } catch (e) {
          if (!(e instanceof Exit) || e.code !== 0) { fail(e); return; }
        }
        started();
      }, e => fail(e));
    }

    return {
      ready,
      files,
      stop() {
        stopped = true; cancelAnimationFrame(raf);
        for (const [t, ty, fn] of listeners) t.removeEventListener(ty, fn);
      },
    };
  }

  window.PRRuntime = { start };
})();
