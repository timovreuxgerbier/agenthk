// review.js — Review (one item per screen, contract rule 4) and Done.
// Reads review.json's shape (SAMPLE_REVIEW for now). Writes decisions.json's shape.
// Pip's words come from the model, which reads text INSIDE screenshots, so every
// piece of it is escaped with esc() and never treated as code.

function esc(t) { var d = document.createElement("div"); d.textContent = t == null ? "" : String(t); return d.innerHTML; }
var GROUPS = [["py", "Needs your OK"], ["pr", "My suggestion"], ["pb", "Set aside"]];
function group(it) {
  if (it.state === "locked") return 2;
  return (it.needs_ok || it.state === "copy") ? 0 : 1;
}
function localTime() { var t = new Date(); t.setMinutes(t.getMinutes() - t.getTimezoneOffset()); return t.toISOString().slice(0, 19); }
var queue = [], pos = 0, decisions = [], started = 0, last = null;

function startReview() {
  queue = SAMPLE_REVIEW.items.slice().sort(function (a, b) {
    return group(a) - group(b) || KIND_ORDER.indexOf(a.kind) - KIND_ORDER.indexOf(b.kind);
  });
  pos = 0; decisions = []; last = null; started = Date.now();
  show("s-review"); card();
}
document.addEventListener("click", function (e) { if (e.target.closest("[data-review]")) startReview(); });

function preview(it) {
  if (it.state === "locked") return "<div class='preview locked' id='pv'><svg width='40' height='40' viewBox='0 0 24 24' fill='none' stroke='#8FB5F2' stroke-width='2' aria-hidden='true'><rect x='5' y='11' width='14' height='10' rx='2'/><path d='M8 11V7a4 4 0 0 1 8 0v4'/></svg>" +
    "<p style='margin:0'>Hidden on purpose.</p><button id='showme'>Show me this screenshot</button></div>";
  var p = SAMPLE_PREVIEWS[it.id];
  return "<div class='preview'><span class='muted'>" + esc(p[0]) + "</span><div class='bubble'>" + esc(p[1]) + "</div>" +
    "<span class='muted' style='font-size:13px'>" + esc(it.file) + " · " + esc(it.file_date) + "</span></div>";
}
function details(it) {
  var g = GROUPS[group(it)], h = "<span class='pill " + g[0] + "'>" + g[1] + "</span>";
  if (it.state === "locked") return h + "<h2 style='font-size:24px'>" + esc(KIND_COPY[it.kind]) + "</h2>" +
    "<p class='muted' style='margin:0'>Taken " + esc(it.file_date) + ". I won't read it, rename it or turn it into text. What should happen to it?</p>" +
    "<div class='row'><button class='calm' data-act='keep_image'>Keep it as it is</button><button data-act='to_be_deleted'>Move to To Be Deleted</button><button data-act='skip'>Not now</button></div>";
  if (it.state === "copy") return h + "<h2 style='font-size:24px'>Exact copy of " + esc(it.copy_of) + "</h2>" +
    "<p class='muted' style='margin:0'>Same picture, pixel for pixel. The original stays.</p>" +
    "<p style='margin:0'>My suggestion: <span class='pill pg'>" + ACTION_WORDS.to_be_deleted + "</span></p>" +
    "<div class='row'><button class='calm' data-act='approve'>Yes, move the copy</button><button data-act='keep_image'>Keep both</button><button data-act='skip'>Not now</button></div>";
  var named = it.action !== "to_be_deleted";
  return h + "<div><p class='eyebrow' style='color:var(--muted)'>What it is</p><p style='margin:4px 0 0;font-size:19px'>" + esc(it.reason) + "</p></div>" +
    "<div class='guess'><span class='pill pg'>Guess</span><p style='margin:6px 0 0'>" + esc(it.why_saved) + "</p></div>" +
    "<p style='margin:0'>My suggestion: <span class='pill pg' id='sugg'>" + ACTION_WORDS[it.action] + "</span></p>" +
    "<div class='field' id='namebox'" + (named ? "" : " hidden") + "><label for='nm'>New name</label><input id='nm' value='" + esc(it.new_name || "") + "'></div>" +
    "<div id='changer' hidden>" + ["keep_image", "keep_text", "to_be_deleted"].map(function (a) {
      return "<label class='choice'><input type='radio' name='act' value='" + a + "'" + (a === it.action ? " checked" : "") + "><span>" + ACTION_WORDS[a] + "</span></label>";
    }).join("") + "</div>" +
    "<div class='row' id='btns'><button class='calm' data-act='approve'>Yes, do this</button><button data-act='change'>Change</button><button data-act='skip'>Not now</button></div>";
}
function card() {
  if (pos >= queue.length) return done();
  var it = queue[pos], el = document.getElementById("s-review");
  el.innerHTML = "<div class='rhead'><div style='flex:1;min-width:260px'><p class='eyebrow'>Review · " + (pos + 1) + " of " + queue.length + "</p>" +
    "<div class='track' style='margin-top:8px;max-width:420px'><div class='fill' style='width:" + Math.round(pos / queue.length * 100) + "%'></div></div></div>" +
    (last ? "<span class='muted'>Saved: " + esc(last) + " <button id='undo' style='min-height:36px;font-size:14px'>Undo</button></span>" : "") +
    "<button id='stop'>Stop here</button></div>" +
    "<div class='rgrid'>" + preview(it) + "<div style='display:flex;flex-direction:column;gap:16px'>" + details(it) + "</div></div>" +
    "<p class='muted' style='margin:0'>Stopping loses nothing: anything you skip comes back next time.</p>";
  wire(it);
  var f = el.querySelector(".calm"); if (f) f.focus();
}
function wire(it) {
  var el = document.getElementById("s-review");
  document.getElementById("stop").onclick = done;
  var u = document.getElementById("undo"); if (u) u.onclick = function () { decisions.pop(); pos--; last = null; card(); };
  var sm = document.getElementById("showme"); if (sm) sm.onclick = function () {
    document.getElementById("pv").innerHTML = "<p class='muted' style='margin:0'>You asked to see it. (The real screenshot appears here.)</p>"; };
  el.querySelectorAll("[data-act]").forEach(function (b) { b.onclick = function () { act(it, b.getAttribute("data-act")); }; });
  el.querySelectorAll("input[name=act]").forEach(function (r) { r.onchange = function () {
    document.getElementById("namebox").hidden = r.value === "to_be_deleted"; }; });
}
function act(it, a) {
  var nm = document.getElementById("nm"), name = nm && !document.getElementById("namebox").hidden ? nm.value.trim() || null : null;
  if (a === "change") {
    document.getElementById("changer").hidden = false;
    document.getElementById("btns").innerHTML = "<button class='calm' data-act='save'>Save change</button><button data-act='skip'>Not now</button>";
    wire(it); return;
  }
  var d = { id: it.id, decision: "approve", action: it.action, new_name: it.state === "open" ? name : null, time: localTime() };
  if (a === "save") { d.action = document.querySelector("input[name=act]:checked").value; d.decision = "change"; if (d.action === "to_be_deleted") d.new_name = null; }
  if (a === "keep_image" || a === "to_be_deleted") { d.decision = "change"; d.action = a; d.new_name = null; }
  if (a === "skip") { d.decision = "skip"; d.action = null; d.new_name = null; }
  if (d.decision === "approve" && it.state === "open" && name !== it.new_name) d.decision = "change";
  decisions.push(d); last = d.decision === "skip" ? "not now" : ACTION_WORDS[d.action];
  pos++; card();
}
function done() {
  var keep = 0, del = 0, later = queue.length;
  decisions.forEach(function (d) { if (d.action === "to_be_deleted") { del++; later--; } else if (d.action) { keep++; later--; } });
  var mins = Math.max(1, Math.round((Date.now() - started) / 60000));
  document.getElementById("s-done").innerHTML = "<div class='narrow' style='display:flex;flex-direction:column;gap:22px;margin-top:30px'>" +
    "<p class='eyebrow'>pip@shift ~ % done</p><h1>" + (later ? "Good place to stop" : "All done for this week") + "</h1>" +
    "<div class='stats'><div class='stat'><span class='muted'>To keep</span><b>" + keep + "</b></div><div class='stat'><span class='muted'>To Be Deleted folder</span><b>" + del + "</b></div><div class='stat'><span class='muted'>Next time</span><b>" + later + "</b></div></div>" +
    "<p class='sub'>Your choices are saved. Only what you approved will move. Nothing is deleted: you empty the To Be Deleted folder yourself, whenever you like.</p>" +
    "<p class='muted' style='margin:0'>Your time: about " + mins + " min.</p>" +
    "<div class='row'><button class='go' data-go='s-welcome'>Close</button><button id='dl'>Download decisions.json (prototype)</button></div></div>";
  document.getElementById("dl").onclick = function () {
    var out = { contract: "0.2", run_id: SAMPLE_REVIEW.run_id, decisions: decisions };
    var a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([JSON.stringify(out, null, 2)], { type: "application/json" }));
    a.download = "decisions.json"; a.click();
  };
  show("s-done");
}
