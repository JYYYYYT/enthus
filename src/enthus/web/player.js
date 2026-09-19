// Playback accounting describes browser scheduling, never proof of hearing.
export class Player {
  constructor(context, report, limit = 2) {
    this.context = context;
    this.report = report;
    this.limit = limit;
    this.pending = new Map();
    this.invalid = new Set();
    this.next = 0;
  }

  enqueue(event) {
    if (this.invalid.has(event.output_id)) return;
    const bytes = Uint8Array.from(atob(event.data), c => c.charCodeAt(0));
    const pcm = new DataView(bytes.buffer);
    const duration = bytes.length / 48000;
    const start = Math.max(this.context.currentTime, this.next);
    if (start + duration - this.context.currentTime > this.limit) {
      throw new Error("Playback queue limit reached; session stopped.");
    }
    const buffer = this.context.createBuffer(1, bytes.length / 2, 24000);
    const channel = buffer.getChannelData(0);
    for (let i = 0; i < channel.length; i++) channel[i] = pcm.getInt16(i * 2, true) / 32768;
    const node = this.context.createBufferSource();
    node.buffer = buffer;
    node.connect(this.context.destination);
    const item = {node, event, start, end: start + duration};
    this.pending.set(event.chunk_id, item);
    node.onended = () => {
      if (!this.pending.delete(event.chunk_id)) return;
      node.disconnect();
      this.report("played", event);
    };
    node.start(start);
    this.next = item.end;
    this.report("queued", event);
  }

  cancel(outputs = [...new Set([...this.pending.values()].map(p => p.event.output_id))]) {
    for (const id of outputs) this.invalid.add(id);
    const now = this.context.currentTime;
    for (const [id, item] of this.pending) {
      if (!this.invalid.has(item.event.output_id)) continue;
      this.pending.delete(id);
      item.node.stop();
      item.node.disconnect();
      this.report(now > item.start ? "uncertain" : "cancelled", item.event);
    }
    this.next = Math.max(now, ...[...this.pending.values()].map(p => p.end));
    return outputs;
  }
}
