// review.js — Review (one item per screen, contract rule 4) and Done.
// Reads review.json's shape (SAMPLE_REVIEW for now). Writes decisions.json's shape.
// Rick's words come from the model, which reads text INSIDE screenshots, so all of
// it goes through esc() and is never treated as code.

function esc(t) {   // safe inside text AND inside quoted attributes (file names can contain ' or ")
  var d = document.createElement("div"); d.textContent = t == null ? "" : String(t);
  return d.innerHTML.replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}
function niceDate(d) { var m = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"], p = String(d).split("-"); return p.length === 3 ? (+p[2]) + " " + m[+p[1] - 1] : esc(d); }
function localTime() { var t = new Date(); t.setMinutes(t.getMinutes() - t.getTimezoneOffset()); return t.toISOString().slice(0, 19); }
// group: 0 needs your OK (Bloop), 1 Rick's suggestion, 2 locked (Zippy)
var GROUPS = [["py", "Needs your OK", "bloop", "tilt"], ["pr", "Rick's suggestion", "pip", "hop"], ["pb", "Locked", "zippy", "nod"]];
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

// A preview is either a real screenshot ({img, label}, written by dev/make_review.py)
// or, in sample data, a few words standing in for it ([app, text]).
function shot(p, alt) {
  return "<img src='" + esc(encodeURI(p.img)) + "' alt='" + esc(alt) + "'><span class='small'>" + esc(p.label) + "</span>";
}
function noBrokenImages(el) {      // if a screenshot file is missing, say so instead of a broken icon
  el.querySelectorAll(".preview img").forEach(function (im) { im.onerror = function () {
    var t = document.createElement("p"); t.className = "small"; t.textContent = "Image not found: " + im.getAttribute("src");
    im.replaceWith(t); }; });
}
function preview(it) {
  var p = SAMPLE_PREVIEWS[it.id] || {};
  if (it.state === "locked") return "<div class='preview locked' id='pv'>" + buddy("zippy", 64) +
    "<p style='margin:0'>Hidden on purpose.</p><button class='quiet' id='showme'>Show me</button></div>";
  if (p.img) return "<div class='preview'>" + shot(p, "Screenshot: " + (it.reason || it.file)) + "</div>";
  return "<div class='preview'><span class='small'>" + esc(p[0]) + "</span><div class='bubble'>" + esc(p[1]) + "</div></div>";
}
// Each card returns its content (top) and its buttons (bar). The bar always sits in the
// same place at the bottom. ALL options show; the suggested one glows in its buddy's colour
// and says "Suggested" in words, so colour is never the only signal. One click decides.
var ICONS = {
  keep_image: "<svg width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' aria-hidden='true'><rect x='3' y='5' width='18' height='14' rx='2'/><circle cx='9' cy='10' r='2'/><path d='M21 16l-5-5-8 8'/></svg>",
  keep_text: "<svg width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' aria-hidden='true'><path d='M5 6h14M5 11h14M5 16h9'/></svg>",
  to_be_deleted: "<svg width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' aria-hidden='true'><path d='M3 7h6l2 2h10v10H3z'/><path d='M10 14h6M13 11l3 3-3 3'/></svg>"
};
function opt(action, label, act, colour, suggested) {
  return "<button class='opt" + (suggested ? " sugg c-" + colour : "") + "' data-act='" + act + "'>" + ICONS[action] +
    "<span>" + label + "</span>" + (suggested ? "<span class='tag'>Suggested</span>" : "") + "</button>";
}
function details(it) {
  var gi = group(it), g = GROUPS[gi], colour = ["y", "r", "b"][gi];
  var h = "<div class='row'>" + buddy(g[2], 40, "who") + "<span class='pill " + g[0] + "'>" + g[1] + "</span></div>";
  var later = "<button class='quiet' data-act='skip'>Not now</button><span class='spacer'></span>";
  if (it.state === "locked") return { top: h + "<h1 style='font-size:28px'>" + esc(KIND_COPY[it.kind] || KIND_COPY.gate_error) + "</h1>" +
    "<p class='sub'>Taken " + niceDate(it.file_date) + ". What should happen to it?</p>",
    bar: later + opt("keep_image", "Keep it", "keep_image", colour, false) + opt("to_be_deleted", ACTION_WORDS.to_be_deleted, "to_be_deleted", colour, false) };
  if (it.state === "copy") return { top: h + "<h1 style='font-size:28px'>A copy of " + esc(it.copy_of) + "</h1>" +
    "<p class='sub'>Same picture. The original stays either way.</p>",
    bar: later + opt("keep_image", "Keep both", "keep_image", colour, false) + opt("to_be_deleted", "Move the copy", "approve", colour, true) };
  return { top: h + "<p class='reason' style='font-size:20px;color:var(--text)'>" + esc(it.reason) + "</p>" +
    "<div class='guess'><span class='pill pg'>Guess</span> " + esc(it.why_saved) + "</div>" +
    "<div class='field' id='namebox'><label for='nm'>Name, if you keep it</label><input id='nm' value='" + esc(it.new_name || "") + "'></div>",
    bar: later + ["keep_image", "keep_text", "to_be_deleted"].map(function (a) {
      return opt(a, ACTION_WORDS[a], a === it.action ? "approve" : "to:" + a, colour, a === it.action);
    }).join("") };
}
function card() {
  if (pos >= queue.length) return done();
  var it = queue[pos], el = document.getElementById("s-review"), c = details(it);
  el.innerHTML = "<div class='rhead'><div class='row'><span class='sample'>" + esc(window.REVIEW_SOURCE || "Sample data") + "</span><span class='small'>" + (pos + 1) + " of " + queue.length + "</span></div>" +
    (last ? "<div class='row small'>" + buddy("pip", 26, "saved") + "Saved <button class='quiet' id='undo' style='min-height:36px'>Undo</button></div>" : "") +
    "<button class='quiet' id='stop'>Stop here</button></div>" +
    "<div class='track' style='margin-bottom:24px'><div class='fill' style='width:" + Math.round(pos / queue.length * 100) + "%'></div></div>" +
    "<div class='rgrid'>" + preview(it) + "<div style='display:flex;flex-direction:column;gap:16px'>" + c.top + "</div></div>" +
    "<div class='abar' id='bar'>" + c.bar + "</div>";
  wire(it);
  react(el.querySelector(".saved"), "hop");                       // approved: Rick hops
  react(el.querySelector(".who"), GROUPS[group(it)][3]);           // arriving: locked nods, unsure tilts
  var m = el.querySelector(".abar .sugg") || el.querySelector(".abar .opt"); if (m) m.focus();
}
function wire(it) {
  var el = document.getElementById("s-review");
  document.getElementById("stop").onclick = done;
  var u = document.getElementById("undo"); if (u) u.onclick = function () { decisions.pop(); pos--; last = null; card(); };
  noBrokenImages(el);
  var sm = document.getElementById("showme"); if (sm) sm.onclick = function () {   // shown only because the person asked
    var p = SAMPLE_PREVIEWS[it.id] || {};
    document.getElementById("pv").innerHTML = p.img ? shot(p, "Locked screenshot you asked to see") :
      "<p class='small'>You asked to see it. (The real screenshot appears here.)</p>";
    noBrokenImages(document.getElementById("pv")); };
  el.querySelectorAll("[data-act]").forEach(function (b) { b.onclick = function () { act(it, b.getAttribute("data-act")); }; });
}
function act(it, a) {
  var nm = document.getElementById("nm"), name = nm ? nm.value.trim() || null : null;
  var d = { id: it.id, decision: "approve", action: it.action, new_name: it.state === "open" ? name : null, time: localTime() };
  if (a.indexOf("to:") === 0) { d.decision = "change"; d.action = a.slice(3); }
  if (a === "keep_image" || a === "to_be_deleted") { d.decision = "change"; d.action = a; d.new_name = null; }
  if (a === "skip") { d.decision = "skip"; d.action = null; d.new_name = null; }
  if (d.action === "to_be_deleted") d.new_name = null;
  if (d.decision === "approve" && it.state === "open" && d.action !== "to_be_deleted" && name !== it.new_name) d.decision = "change";
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
