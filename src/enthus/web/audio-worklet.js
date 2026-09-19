class Microphone extends AudioWorkletProcessor {
  constructor() {
    super();
    this.samples = new Int16Array(1600);
    this.used = 0;
  }
  process(inputs) {
    const channel = inputs[0]?.[0];
    if (channel) {
      for (const sample of channel) {
        this.samples[this.used++] = Math.round(Math.max(-1, Math.min(1, sample)) * 32767);
        if (this.used === this.samples.length) {
          this.port.postMessage({samples: this.samples, time: currentTime});
          this.samples = new Int16Array(1600);
          this.used = 0;
        }
      }
    }
    return true;
  }
}
registerProcessor("microphone", Microphone);
