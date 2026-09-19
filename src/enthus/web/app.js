import {Player} from "./player.js";

const el = id => document.getElementById(id);
const config = await fetch("/config").then(r => r.json());
el("configuration").textContent = config.configured
  ? `${config.model} · 120 s session · 1 frame/s · metadata only`
  : "Set GEMINI_API_KEY on the local host and restart it to enable a live session.";
el("start").disabled = !config.configured;
let session = null;
let trace = [];
function record(kind, data = {}) {
  trace.push({kind, at: Date.now() / 1000, ...data});
  if (trace.length > 5000) trace.shift();
}
function note(text) {
  el("events").textContent = `${new Date().toLocaleTimeString()} ${text}\n${el("events").textContent}`.slice(0, 6000);
}
function send(s, message) {
  if (session !== s || s.socket?.readyState !== WebSocket.OPEN) return;
  if (s.socket.bufferedAmount > 128000) throw new Error("Input connection congested.");
  s.socket.send(JSON.stringify(message));
}
function sensors(s) {
  el("sensors").textContent = `Screen: ${s.screen ? "sharing" : "off"} · Microphone: ${s.mic ? "sharing" : "off"}`;
}
function cleanupStream(stream) {
  stream?.getTracks().forEach(track => track.stop());
}
function stop(reason = "Session ended.") {
  const s = session;
  if (!s) return;
  session = null; // Invalidate callbacks before asynchronous teardown.
  clearInterval(s.frames); clearInterval(s.heartbeat); clearTimeout(s.deadline);
  cleanupStream(s.screen); cleanupStream(s.mic);
  s.screen = s.mic = null;
  s.player?.cancel();
  s.worklet?.disconnect(); s.source?.disconnect();
  if (s.socket?.readyState === WebSocket.OPEN) {
    s.socket.send(JSON.stringify({type: "end"}));
    // Leave a short metadata-only drain window for the final host trace.
    setTimeout(() => s.socket.close(), 1000);
  } else s.socket?.close();
  void s.input?.close(); void s.output?.close();
  el("preview").srcObject = null;
  sensors(s);
  for (const id of ["speech", "screen", "microphone", "end"]) el(id).disabled = true;
  el("start").disabled = !config.configured;
  el("status").textContent = `${reason} Screen and microphone are off.`;
  record("local_end", {reason}); note(reason);
}
function encode(bytes) {
  let text = "";
  for (const byte of bytes) text += String.fromCharCode(byte);
  return btoa(text);
}
function stopSensor(sensor) {
  const s = session;
  if (!s) return;
  if (!s.ready) { stop("A selected sensor stopped during setup."); return; }
  const key = sensor === "video" ? "screen" : "mic";
  cleanupStream(s[key]); s[key] = null;
  if (sensor === "video") el("preview").srcObject = null;
  el(sensor === "video" ? "screen" : "microphone").disabled = true;
  // Invalidate all local pending playback immediately, before host acknowledgement.
  const ids = s.player?.cancel() || [];
  if (s.currentOutput !== null && !ids.includes(s.currentOutput)) ids.push(s.currentOutput);
  s.player?.cancel(ids);
  try {
    send(s, {type: "stop_speech", output_ids: ids});
    send(s, {type: "stop_sensor", sensor});
  } catch { stop("Control connection failed."); }
  sensors(s); record("local_revoke", {sensor}); note(`${sensor} stopped for this session.`);
}
async function start() {
  if (session) return;
  trace = [];
  const s = {screen: null, mic: null, ready: false, currentOutput: null, lastHost: Date.now()};
  session = s;
  s.deadline = setTimeout(() => { if (session === s) stop("Session duration limit reached."); }, config.seconds * 1000);
  el("start").disabled = true; el("end").disabled = false;
  el("status").textContent = "Choose a sketch window/tab and allow the microphone. No media is sent until connected.";
  try {
    s.output = new AudioContext({sampleRate: 24000});
    await s.output.resume();
    if (session !== s) return;
    const screen = await navigator.mediaDevices.getDisplayMedia({video: true, audio: false});
    if (session !== s) { cleanupStream(screen); return; }
    s.screen = screen;
    screen.getVideoTracks()[0].onended = () => { if (session === s) stopSensor("video"); };
    screen.getVideoTracks()[0].onmute = () => { if (session === s) stop("Screen input became unavailable."); };
    const mic = await navigator.mediaDevices.getUserMedia({audio: {
      channelCount: 1, echoCancellation: true, noiseSuppression: true,
    }, video: false});
    if (session !== s) { cleanupStream(mic); return; }
    s.mic = mic;
    mic.getAudioTracks()[0].onended = () => { if (session === s) stopSensor("audio"); };
    mic.getAudioTracks()[0].onmute = () => { if (session === s) stop("Microphone input became unavailable."); };
    // A browser picker may remain open after End; never use its late grant.
    if (!s.screen?.active || !s.mic.active) throw new Error("A selected sensor stopped before connection.");
    sensors(s);
    el("preview").srcObject = screen;
    await el("preview").play();
    if (session !== s) return;
    const videoElement = el("preview");
    if (!videoElement.requestVideoFrameCallback) throw new Error("Use a browser supporting video-frame callbacks.");
    function decodedFrame() {
      if (session !== s || !s.screen) return;
      s.lastDecodedFrame = Date.now() / 1000;
      videoElement.requestVideoFrameCallback(decodedFrame);
    }
    videoElement.requestVideoFrameCallback(decodedFrame);
    s.player = new Player(s.output, (status, event) => {
      record("playback_report", {status, output_id: event.output_id, chunk_id: event.chunk_id});
      try { send(s, {type: "playback", status, output_id: event.output_id, chunk_id: event.chunk_id}); }
      catch { stop("Playback reporting connection failed."); }
    });
    s.input = new AudioContext({sampleRate: 16000});
    if (s.input.sampleRate !== 16000) throw new Error("This browser cannot capture at 16 kHz.");
    await s.input.audioWorklet.addModule("/audio-worklet.js");
    await s.input.resume();
    if (session !== s) { await s.input.close(); return; }
    for (const context of [s.input, s.output]) context.onstatechange = () => {
      if (session === s && s.ready && context.state !== "running") stop("Browser audio became unavailable.");
    };
    const audioEpoch = Date.now() / 1000 - s.input.currentTime;
    s.source = s.input.createMediaStreamSource(mic);
    s.worklet = new AudioWorkletNode(s.input, "microphone");
    s.source.connect(s.worklet);
    // The worklet produces silence; connecting it keeps capture processing active.
    s.worklet.connect(s.input.destination);
    s.worklet.port.onmessage = event => {
      if (session !== s || !s.ready || !s.mic) return;
      try {
        const samples = event.data.samples;
        const bytes = new Uint8Array(samples.length * 2);
        const view = new DataView(bytes.buffer);
        samples.forEach((sample, i) => view.setInt16(i * 2, sample, true));
        send(s, {type: "media", sensor: "audio", captured_at: audioEpoch + event.data.time,
                 data: encode(bytes)});
      } catch { stop("Audio connection congested."); }
    };
    s.socket = new WebSocket(`ws://${location.host}/session`);
    s.socket.onopen = () => {
      if (session !== s) { s.socket.close(); return; }
      send(s, {type: "start", token: config.token, audio: true, video: true});
    };
    s.socket.onmessage = event => {
      const data = JSON.parse(event.data);
      if (data.kind === "ended") {
        record("host_trace", {session_id: data.session_id, events: data.trace});
        if (session === s) stop(`Host ended: ${data.reason}.`);
        return;
      }
      if (session !== s) return;
      s.lastHost = Date.now();
      if (data.kind === "heartbeat") return;
      const {data: media, ...metadata} = data;
      record("host_event", metadata);
      try {
        if (data.kind === "ready") {
          s.ready = true; s.player.limit = data.limits.queue_seconds;
          el("status").textContent = "Sharing is active. A reply ending does not end the session.";
          for (const id of ["speech", "screen", "microphone"]) el(id).disabled = false;
          note("Model connected. Capture continues across turns.");
        } else if (data.kind === "audio") {
          s.currentOutput = data.output_id;
          s.player.enqueue(data);
        } else if (["interrupted", "revoked"].includes(data.kind)) {
          s.player.cancel([data.output_id]);
          note(data.kind);
        } else if (data.kind === "cancelled") {
          s.player.cancel(data.output_ids);
        } else if (data.kind === "turn_complete") {
          if (s.currentOutput === data.output_id) s.currentOutput = null;
          note("Reply complete; still receiving the shared environment.");
        }
      } catch (error) { stop(error.message); }
    };
    s.socket.onerror = () => { if (session === s) stop("Connection failed. Check the local model configuration."); };
    s.socket.onclose = () => { if (session === s) stop("Model connection closed."); };
    const frame = document.createElement("canvas");
    const context = frame.getContext("2d");
    s.frames = setInterval(() => {
      if (session !== s || !s.ready || !s.screen) return;
      const video = el("preview");
      if (!video.videoWidth || video.readyState < 2) return;
      if (!s.lastDecodedFrame || Date.now() / 1000 - s.lastDecodedFrame > 1) {
        stop("No fresh shared video frame is available."); return;
      }
      const scale = Math.min(1, 768 / Math.max(video.videoWidth, video.videoHeight));
      frame.width = Math.round(video.videoWidth * scale); frame.height = Math.round(video.videoHeight * scale);
      context.drawImage(video, 0, 0, frame.width, frame.height);
      const captured = s.lastDecodedFrame;
      const data = frame.toDataURL("image/jpeg", .6).split(",")[1];
      if (data.length > 133332) { stop("Shared frame exceeds the media limit."); return; }
      try {
        send(s, {type: "media", sensor: "video", captured_at: captured, data});
        el("freshness").textContent = `Last frame sent: ${new Date().toLocaleTimeString()} · ${frame.width} × ${frame.height}`;
        record("frame_sent", {captured_at: captured});
      } catch { stop("Visual connection congested."); }
    }, 1050);
    s.heartbeat = setInterval(() => {
      if (session !== s) return;
      if (s.ready && Date.now() - s.lastHost > 5000) { stop("Host heartbeat lost."); return; }
      try { send(s, {type: "heartbeat"}); } catch { stop("Host connection congested."); }
    }, 1000);
  } catch (error) { if (session === s) stop(`Could not start: ${error.message}`); }
}
el("start").onclick = start;
el("end").onclick = () => stop();
el("screen").onclick = () => stopSensor("video");
el("microphone").onclick = () => stopSensor("audio");
el("speech").onclick = () => {
  const s = session;
  if (!s?.player) return;
  const ids = s.player.cancel();
  if (s.currentOutput !== null && !ids.includes(s.currentOutput)) ids.push(s.currentOutput);
  s.player.cancel(ids);
  try { send(s, {type: "stop_speech", output_ids: ids}); }
  catch { stop("Control connection failed."); }
  record("local_stop_speech", {output_ids: ids}); note("Current speech stopped; sensors remain as shown.");
};
el("export").onclick = () => {
  const url = URL.createObjectURL(new Blob([JSON.stringify({variant: "thin_baseline", model: config.model, trace}, null, 2)], {type: "application/json"}));
  const link = document.createElement("a"); link.href = url; link.download = "enthus-presence-trace.json";
  link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
};
window.addEventListener("pagehide", () => stop("Page closed."));
const sketch = el("sketch"), pen = sketch.getContext("2d");
function clear() {
  pen.fillStyle = "#f7faf6"; pen.fillRect(0, 0, sketch.width, sketch.height);
  pen.strokeStyle = "#315b48"; pen.lineWidth = 4;
  pen.strokeRect(70, 90, 180, 130); pen.strokeRect(440, 230, 190, 130);
  pen.fillStyle = "#315b48"; pen.font = "24px system-ui";
  pen.fillText("START", 100, 165); pen.fillText("GOAL", 485, 305);
}
let drawing = false;
function point(e) { const r = sketch.getBoundingClientRect(); return [(e.clientX-r.left)*sketch.width/r.width, (e.clientY-r.top)*sketch.height/r.height]; }
sketch.onpointerdown = e => { drawing = true; sketch.setPointerCapture(e.pointerId); pen.beginPath(); pen.moveTo(...point(e)); };
sketch.onpointermove = e => { if (drawing) { pen.lineTo(...point(e)); pen.stroke(); } };
sketch.onpointerup = sketch.onpointercancel = () => { drawing = false; };
el("clear").onclick = clear;
el("obstacle").onclick = () => { pen.fillStyle = "#b96a47"; pen.fillRect(300, 160, 100, 170); };
clear();
