// setup.js — Setup 1 "Get Shyft ready": check Ollama and the two models, and get what's missing.
// Two modes:
//  - LIVE (opened by app/shyft_app.py): real answers from this computer (live.js). Stage 2 downloads
//    missing model files through Ollama (live_jobs.js). Ollama itself the person installs. Every judgement (ready, enough
//    space) comes from the server, so this screen and the Spec screen always agree.
//  - PROTOTYPE (opened as a file): simulated, for design demos. Pick a scenario in the prototype menu.
// Values from the server go onto the page as text, never as markup.

var NEED = [
  { id: "ollama", name: "The Ollama app", what: "Runs Rick and Zippy on this computer. Free." },
  { id: "zippy",  name: "Zippy's model",  what: "gemma4:e4b-it-q4_K_M · spots private screenshots" },
  { id: "rick",   name: "Rick's model",   what: "gemma4:e2b-it-q4_K_M · suggests what to do" }
];
var have = {}, pct = {}, busy = false, timers = [], liveNote = "";
function later(fn, ms) { timers.push(setTimeout(fn, ms)); }   // every timer is tracked so it can be stopped

// ---- PROTOTYPE ----
var SCENARIOS = { ready: ["ollama", "zippy", "rick"], models: ["ollama"], nothing: [] };
function setScenario(name) {
  if (window.LIVE) return liveCheck();                // real answers instead of a made-up scenario
  timers.forEach(clearTimeout); timers = [];          // stop any fake download still running
  have = {}; pct = {}; busy = false;
  var note = document.getElementById("need-note"); if (note) note.textContent = "";
  (SCENARIOS[name] || []).forEach(function (id) { have[id] = "ready"; });
  NEED.forEach(function (n) { if (!have[n.id]) have[n.id] = "missing"; });
  renderNeeds();
}

// ---- LIVE: what is true on this computer ----
var LIVE_WORDS = {   // our own markup only; every state has words, never colour alone
  notrunning: "<span class='miss'>Not running</span>",
  old: "<span class='miss'>Too old for Shyft</span>",
  cloudon: "<span class='miss'>Cloud is on</span>",
  missing: "<span class='miss'>Not downloaded yet</span>",
  wrong: "<span class='miss'>Different build</span>",
  checking: "<span class='wait'>Checking…</span>"
};
function liveCheck() {
  NEED.forEach(function (n) { have[n.id] = "checking"; }); renderNeeds();
  liveGet("/api/status", function (s, why) {
    if (!s) { liveNote = "Couldn't reach Shyft's helper (" + why + "). Is its window still open?"; NEED.forEach(function (n) { have[n.id] = "missing"; }); return renderNeeds(); }
    var o = s.ollama, notes = [];
    // Ready only if a run would really start: running, able to report its cloud, and the cloud off
    // (Shyft's cloud lock refuses every run otherwise).
    have.ollama = !o.running ? "notrunning" : o.cloud === "too_old" ? "old" : o.cloud === "on" ? "cloudon" : "ready";
    s.models.forEach(function (m) {
      var id = m.role === "gate" ? "zippy" : "rick";
      NEED.filter(function (n) { return n.id === id; })[0].what = (m.matches ? m.name : m.pull) + " · " + (id === "zippy" ? "spots private screenshots" : "suggests what to do");
      have[id] = !m.found ? "missing" : m.matches ? "ready" : "wrong";
    });
    if (have.ollama === "notrunning") notes.push("Open Ollama (the llama icon), then check again.");
    if (have.ollama === "old") notes.push("This Ollama can't say whether its cloud is off, and Shyft checks that before every run. Update it from ollama.com/download.");
    if (have.ollama === "cloudon") notes.push("Ollama's cloud is on, so Shyft would refuse to run. " + o.cloud_fix);
    if (have.zippy === "wrong" || have.rick === "wrong") notes.push("A model here isn't the build Shyft was measured with. Please tell the Shyft team.");
    var c = s.computer, r = s.requirements;
    notes.push("This computer: " + (c.memory_gb == null ? "memory couldn't be checked" : c.memory_gb + " GB memory") + ", " +
      (c.free_disk_gb == null ? "free space couldn't be checked" : c.free_disk_gb + " GB free") + ". " +
      (allReady() ? "" : "Needed now: about " + r.need_now_gb + " GB free" + (s.meets.disk === false ? ", so not enough yet." : ".")));
    liveNote = notes.join("\n");   // one note per line (screens.css: #need-help keeps the line breaks)
    renderNeeds();
  });
}

// ---- Shared ----
function canDownload() {   // live: Ollama ready, and a model simply missing (a different build is never replaced)
  return have.ollama === "ready" && (have.zippy === "missing" || have.rick === "missing"); }
function allReady() { return NEED.every(function (n) { return have[n.id] === "ready"; }); }
function statusHtml(id) {   // our own markup only (no values from the server)
  var s = have[id];
  if (s === "ready") return "<span class='ok'>✓ Ready</span>";
  if (LIVE_WORDS[s]) return LIVE_WORDS[s];
  if (s === "waiting") return "<span class='wait'>Waiting for Ollama to open…</span>";
  if (s === "downloading") return "<span class='dl'><span class='track'><span class='fill' style='width:" + pct[id] + "%'></span></span>" + pct[id] + "%</span>";
  return "<span class='miss'>Not found</span>";
}
function renderNeeds() {
  var list = document.getElementById("needs");
  list.textContent = "";
  NEED.forEach(function (n) {   // names and model names as text; only the status is our own markup
    var li = document.createElement("li"), left = document.createElement("span"), b = document.createElement("b"), small = document.createElement("span");
    b.textContent = n.name; small.className = "small"; small.textContent = n.what;
    left.appendChild(b); left.appendChild(document.createElement("br")); left.appendChild(small);
    var right = document.createElement("span"); right.innerHTML = statusHtml(n.id);
    li.appendChild(left); li.appendChild(right.firstChild || right);
    list.appendChild(li);
  });
  var main = document.getElementById("need-main"), help = document.getElementById("need-help");
  if (window.LIVE) {
    var downloading = have.zippy === "downloading" || have.rick === "downloading";
    main.textContent = allReady() ? "Continue" : downloading ? "Downloading…" : canDownload() ? "Download what's missing" : "Check again";
    main.disabled = downloading;
    help.textContent = liveNote;
    document.getElementById("need-note").textContent = "";
    return;
  }
  main.textContent = allReady() ? "Continue" : busy ? "Downloading…" : "Get what's missing";
  help.innerHTML = have.ollama === "waiting"
    ? "1. Open the Ollama file in your Downloads. 2. Drag it into Applications, then open it. I'll notice and carry on. <button class='quiet' id='opened'>I've opened it</button>"
    : allReady() ? "All set. Nothing more to download." : "An 11.2 GB download. Needs 18 GB free: the download plus room to work.";
  var o = document.getElementById("opened"); if (o) o.onclick = ollamaOpened;
}

function getMissing() {
  if (allReady()) return show("s-folder");
  if (window.LIVE) return canDownload() ? liveGetReady() : liveCheck();   // stage 2: download, or check again
  if (busy || have.ollama === "waiting") return;       // already working on it: don't start twice
  if (have.ollama !== "ready") {
    have.ollama = "waiting"; renderNeeds();
    document.getElementById("need-note").textContent = "Prototype: in the real app this opens ollama.com/download.";
    later(function () { if (have.ollama === "waiting") ollamaOpened(); }, 4000);
    return;
  }
  downloadNext();
}
function ollamaOpened() {
  if (have.ollama !== "waiting") return; have.ollama = "ready"; document.getElementById("need-note").textContent = ""; renderNeeds(); downloadNext(); }
function downloadNext() {
  var next = NEED.filter(function (n) { return have[n.id] === "missing"; })[0];
  if (!next) { busy = false; renderNeeds(); return; }
  busy = true; have[next.id] = "downloading"; pct[next.id] = 0;
  (function tick() {
    pct[next.id] = Math.min(100, pct[next.id] + 4); renderNeeds();
    if (pct[next.id] < 100) return later(tick, 120);    // prototype speed; really 10 to 30 min each
    have[next.id] = "ready"; downloadNext();
  })();
}
document.getElementById("need-main").onclick = getMissing;
var picker = document.getElementById("need-pick");   // prototype menu (no inline handler: the security policy forbids them)
if (picker) picker.onchange = function () { setScenario(this.value); };
setScenario("nothing");
