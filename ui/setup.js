// setup.js — Step 1 "Get Shyft ready": check Ollama and the two models, and get what's missing.
// PROTOTYPE: everything here is simulated. In the real app:
//  - "is Ollama open?"      = ask http://127.0.0.1:11434/api/tags (answers only if Ollama is running)
//  - "is a model there?"    = the same answer lists the downloaded models
//  - "download a model"     = POST http://127.0.0.1:11434/api/pull, which reports progress
// Installing Ollama itself is the one step the person must do: open the file, drag it to Applications.
// Team decision: does the page talk to Ollama for this, or does our Python harness?

var NEED = [
  { id: "ollama", name: "The Ollama app", what: "Runs Rick and Zippy on this computer. Free." },
  { id: "zippy",  name: "Zippy's model",  what: "gemma4:e4b · spots private screenshots" },
  { id: "rick",   name: "Rick's model",   what: "gemma4:e2b · suggests what to do" }
];
var have = {}, pct = {}, busy = false, timers = [];
function later(fn, ms) { timers.push(setTimeout(fn, ms)); }   // every timer is tracked so it can be stopped

// Real check: Ollama answers on this computer only while it is running. Gives up after 1.5 s.
function ollamaRunning(cb) {
  var done = false, finish = function (ok) { if (!done) { done = true; cb(ok); } };
  setTimeout(function () { finish(false); }, 1500);
  fetch("http://127.0.0.1:11434/api/tags").then(function (r) { finish(r.ok); }).catch(function () { finish(false); });
}
var SCENARIOS = { ready: ["ollama", "zippy", "rick"], models: ["ollama"], nothing: [] };

function setScenario(name) {
  timers.forEach(clearTimeout); timers = [];          // stop any fake download still running
  have = {}; pct = {}; busy = false;
  var note = document.getElementById("need-note"); if (note) note.textContent = "";
  (SCENARIOS[name] || []).forEach(function (id) { have[id] = "ready"; });
  NEED.forEach(function (n) { if (!have[n.id]) have[n.id] = "missing"; });
  renderNeeds();
}
function allReady() { return NEED.every(function (n) { return have[n.id] === "ready"; }); }

function statusHtml(id) {
  var s = have[id];
  if (s === "ready") return "<span class='ok'>✓ Ready</span>";
  if (s === "waiting") return "<span class='wait'>Waiting for Ollama to open…</span>";
  if (s === "downloading") return "<span class='dl'><span class='track'><span class='fill' style='width:" + pct[id] + "%'></span></span>" + pct[id] + "%</span>";
  return "<span class='miss'>Not found</span>";
}
function renderNeeds() {
  document.getElementById("needs").innerHTML = NEED.map(function (n) {
    return "<li><span><b>" + n.name + "</b><br><span class='small'>" + n.what + "</span></span>" + statusHtml(n.id) + "</li>";
  }).join("");
  var main = document.getElementById("need-main"), help = document.getElementById("need-help");
  main.textContent = allReady() ? "Continue" : busy ? "Downloading…" : "Get what's missing";
  help.innerHTML = have.ollama === "waiting"
    ? "1. Open the Ollama file in your Downloads. 2. Drag it into Applications, then open it. I'll notice and carry on. <button class='quiet' id='opened'>I've opened it</button>"
    : allReady() ? "All set. Nothing more to download." : "An 11.2 GB download. Needs 18 GB free: the download plus room to work.";
  var o = document.getElementById("opened"); if (o) o.onclick = ollamaOpened;
}

function getMissing() {
  if (allReady()) return show("s-folder");
  if (busy || have.ollama === "waiting") return;       // already working on it: don't start twice
  if (have.ollama !== "ready") {
    // Real app: open the official download page, then check every few seconds whether Ollama answers.
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
setScenario("nothing");
