import assert from "node:assert/strict";
import {test} from "node:test";
import {Player} from "../src/enthus/web/player.js";

function fixture() {
  const nodes = [], reports = [];
  const context = {
    currentTime: 0, destination: {},
    createBuffer: (_, length) => ({getChannelData: () => new Float32Array(length)}),
    createBufferSource: () => {
      const node = {connect() {}, disconnect() {}, start() {}, stop() { this.stopped = true; }};
      nodes.push(node); return node;
    },
  };
  return {context, nodes, reports, player: new Player(context, (status, event) => reports.push({status, id: event.chunk_id}))};
}
const event = (chunk_id, output_id = 1) => ({chunk_id, output_id, data: Buffer.alloc(4800).toString("base64")});

test("S28 stop cancels queued audio, marks partial playback uncertain, and rejects late chunks", () => {
  const f = fixture();
  f.player.enqueue(event(1)); f.player.enqueue(event(2));
  f.context.currentTime = .05;
  f.player.cancel();
  assert.equal(f.nodes.every(n => n.stopped), true);
  assert.deepEqual(f.reports.slice(-2).map(r => r.status), ["uncertain", "cancelled"]);
  f.nodes[0].onended();
  assert.equal(f.reports.some(r => r.status === "played"), false);
  f.player.enqueue(event(3)); assert.equal(f.nodes.length, 2);
  f.player.enqueue(event(4, 2)); assert.equal(f.nodes.length, 3);
});

test("S29 playback queue is bounded and a finished chunk records playback only", () => {
  const f = fixture(); f.player.limit = .15;
  f.player.enqueue(event(1));
  assert.throws(() => f.player.enqueue(event(2)), /queue limit/);
  f.context.currentTime = .1; f.nodes[0].onended();
  assert.equal(f.reports.at(-1).status, "played");
  assert.equal(f.player.pending.size, 0);
});
