// review.js — Review (one item per screen, contract rule 4) and Done.
// Reads review.json's shape (SAMPLE_REVIEW for now). Writes decisions.json's shape.
// Pip's words come from the model, which reads text INSIDE screenshots, so all of
// it goes through esc() and is never treated as code.

function esc(t) { var d = document.createElement("div"); d.textContent = t == null ? "" : String(t); return d.innerHTML; }
function niceDate(d) { var m = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"], p = String(d).split("-"); return p.length === 3 ? (+p[2]) + " " + m[+p[1] - 1] : esc(d); }
function localTime() { var t = new Date(); t.setMinutes(t.getMinutes() - t.getTimezoneOffset()); return t.toISOString().slice(0, 19); }
// group: 0 needs your OK (Bloop), 1 Pip's suggestion, 2 locked (Zippy)
var GROUPS = [["py", "Needs your OK", "bloop", "tilt"], ["pr", "Pip's suggestion", "pip", "hop"], ["pb", "Locked", "zippy", "nod"]];
function group(it) { return it.state === "locked" ? 2 : (it.needs_ok || it.state === "copy") ? 0 : 1; }
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
  if (it.state === "locked") return "<div class='preview locked' id='pv'>" + buddy("zippy", 64) +
    "<p style='margin:0'>Hidden on purpose.</p><button class='quiet' id='showme'>Show me</button></div>";
  var p = SAMPLE_PREVIEWS[it.id];
  return "<div class='preview'><span class='small'>" + esc(p[0]) + "</span><div class='bubble'>" + esc(p[1]) + "</div></div>";
}
function details(it) {
  var g = GROUPS[group(it)], h = "<div class='row'>" + buddy(g[2], 40, "who") + "<span class='pill " + g[0] + "'>" + g[1] + "</span></div>";
  if (it.state === "locked") return h + "<h1 style='font-size:26px'>" + esc(KIND_COPY[it.kind]) + "</h1>" +
    "<p class='sub'>Taken " + niceDate(it.file_date) + ". What should happen to it?</p>" +
    "<div class='row'><button class='main' data-act='keep_image'>Keep it</button><button data-act='to_be_deleted'>Move to To Be Deleted</button><button class='quiet' data-act='skip'>Not now</button></div>";
  if (it.state === "copy") return h + "<h1 style='font-size:26px'>A copy of another screenshot</h1>" +
    "<p class='sub'>The original stays. Move this copy to To Be Deleted?</p>" +
    "<div class='row'><button class='main' data-act='approve'>Yes, move it</button><button data-act='keep_image'>Keep both</button><button class='quiet' data-act='skip'>Not now</button></div>";
  return h + "<h1 style='font-size:26px'>" + esc(it.reason) + "</h1>" +
    "<div class='guess'><span class='pill pg'>Guess</span> " + esc(it.why_saved) + "</div>" +
    "<p style='margin:0'>Suggestion: <b>" + ACTION_WORDS[it.action] + "</b></p>" +
    "<div class='field' id='namebox'" + (it.action === "to_be_deleted" ? " hidden" : "") + "><label for='nm'>Name</label><input id='nm' value='" + esc(it.new_name || "") + "'></div>" +
    "<div id='changer' hidden>" + ["keep_image", "keep_text", "to_be_deleted"].map(function (a) {
      return "<label class='choice'><input type='radio' name='act' value='" + a + "'" + (a === it.action ? " checked" : "") + "><span>" + ACTION_WORDS[a] + "</span></label>";
    }).join("") + "</div>" +
    "<div class='row' id='btns'><button class='main' data-act='approve'>Yes</button><button data-act='change'>Change</button><button class='quiet' data-act='skip'>Not now</button></div>";
}
function card() {
  if (pos >= queue.length) return done();
  var it = queue[pos], el = document.getElementById("s-review");
  el.innerHTML = "<div class='rhead'><div class='row'><span class='sample'>Sample data</span><span class='small'>" + (pos + 1) + " of " + queue.length + "</span></div>" +
    (last ? "<div class='row small'>" + buddy("pip", 26, "saved") + "Saved <button class='quiet' id='undo' style='min-height:36px'>Undo</button></div>" : "") +
    "<button class='quiet' id='stop'>Stop here</button></div>" +
    "<div class='track' style='margin-bottom:24px'><div class='fill' style='width:" + Math.round(pos / queue.length * 100) + "%'></div></div>" +
    "<div class='rgrid'>" + preview(it) + "<div style='display:flex;flex-direction:column;gap:16px'>" + details(it) + "</div></div>";
  wire(it);
  react(el.querySelector(".saved"), "hop");                       // approved: Pip hops
  react(el.querySelector(".who"), GROUPS[group(it)][3]);           // arriving: locked nods, unsure tilts
  var m = el.querySelector(".main"); if (m) m.focus();
}
function wire(it) {
  var el = document.getElementById("s-review");
  document.getElementById("stop").onclick = done;
  var u = document.getElementById("undo"); if (u) u.onclick = function () { decisions.pop(); pos--; last = null; card(); };
  var sm = document.getElementById("showme"); if (sm) sm.onclick = function () {
    document.getElementById("pv").innerHTML = "<p class='small'>You asked to see it. (The real screenshot appears here.)</p>"; };
  el.querySelectorAll("[data-act]").forEach(function (b) { b.onclick = function () { act(it, b.getAttribute("data-act")); }; });
  el.querySelectorAll("input[name=act]").forEach(function (r) { r.onchange = function () {
    document.getElementById("namebox").hidden = r.value === "to_be_deleted"; }; });
}
function act(it, a) {
  var box = document.getElementById("namebox"), nm = document.getElementById("nm");
  var name = nm && box && !box.hidden ? nm.value.trim() || null : null;
  if (a === "change") {
    document.getElementById("changer").hidden = false;
    document.getElementById("btns").innerHTML = "<button class='main' data-act='save'>Save</button><button class='quiet' data-act='skip'>Not now</button>";
    wire(it); document.querySelector("#btns .main").focus(); return;
  }
  var d = { id: it.id, decision: "approve", action: it.action, new_name: it.state === "open" ? name : null, time: localTime() };
  if (a === "save") { d.action = document.querySelector("input[name=act]:checked").value; d.decision = "change"; if (d.action === "to_be_deleted") d.new_name = null; }
  if (a === "keep_image" || a === "to_be_deleted") { d.decision = "change"; d.action = a; d.new_name = null; }
  if (a === "skip") { d.decision = "skip"; d.action = null; d.new_name = null; }
  if (d.decision === "approve" && it.state === "open" && name !== it.new_name) d.decision = "change";
  decisions.push(d); last = d; pos++; card();
}
function done() {
  var keep = 0, del = 0, later = queue.length;
  decisions.forEach(function (d) { if (d.action === "to_be_deleted") { del++; later--; } else if (d.action) { keep++; later--; } });
  document.getElementById("s-done").innerHTML = "<div class='body'>" + trio(48) +
    "<h1>" + (later ? "Good place to stop" : "All done") + "</h1>" +
    "<p class='sub'>" + keep + " kept · " + del + " in To Be Deleted · " + later + " for next time</p>" +
    "<button class='main' data-go='s-welcome'>Close</button>" +
    "<button class='quiet protoonly' id='dl'>Download decisions.json (prototype)</button></div>";
  document.getElementById("dl").onclick = function () {
    var out = { contract: "0.2", run_id: SAMPLE_REVIEW.run_id, decisions: decisions };
    var a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([JSON.stringify(out, null, 2)], { type: "application/json" }));
    a.download = "decisions.json"; a.click();
  };
  show("s-done");
  react(document.querySelector("#s-done .b2"), "hop");
}
