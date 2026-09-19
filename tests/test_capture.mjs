import assert from "node:assert/strict";
import {test} from "node:test";

// Exercise permission races without accessing real browser devices.
async function fixture(id) {
  let grant;
  const permission = new Promise(resolve => { grant = resolve; });
  const pen = {fillRect() {}, strokeRect() {}, fillText() {}};
  const elements = new Map();
  const element = name => {
    if (!elements.has(name)) elements.set(name, {disabled: false, textContent: "", getContext: () => pen});
    return elements.get(name);
  };
  globalThis.document = {getElementById: element};
  globalThis.window = {addEventListener() {}};
  globalThis.fetch = async () => ({json: async () => ({configured: true, model: "synthetic", seconds: 120})});
  let micRequests = 0;
  Object.defineProperty(globalThis, "navigator", {configurable: true, value: {
    mediaDevices: {getDisplayMedia: () => permission, getUserMedia: async () => { micRequests++; }},
  }});
  globalThis.WebSocket = {OPEN: 1};
  globalThis.AudioContext = class {
    async resume() {} async close() {}
  };
  await import(`../src/enthus/web/app.js?test=${id}`);
  return {element, grant, micRequests: () => micRequests};
}

test("S31 End while screen picker is pending disposes the late grant without requesting microphone", async () => {
  const f = await fixture(1);
  const starting = f.element("start").onclick();
  await Promise.resolve();
  f.element("end").onclick();
  let stopped = false;
  f.grant({getTracks: () => [{stop() { stopped = true; }}]});
  await starting;
  assert.equal(stopped, true);
  assert.equal(f.micRequests(), 0);
  assert.match(f.element("status").textContent, /off/);
});

test("S32 duration expiry also covers time spent inside a permission picker", async () => {
  const original = globalThis.setTimeout;
  let expire;
  globalThis.setTimeout = callback => { expire = callback; return 0; };
  try {
    const f = await fixture(2);
    const starting = f.element("start").onclick();
    await Promise.resolve();
    expire();
    let stopped = false;
    f.grant({getTracks: () => [{stop() { stopped = true; }}]});
    await starting;
    assert.equal(stopped, true);
    assert.equal(f.micRequests(), 0);
    assert.match(f.element("status").textContent, /duration limit/);
  } finally { globalThis.setTimeout = original; }
});
