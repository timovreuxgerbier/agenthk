// flow.js — moving between screens: welcome, walkthrough, setup, sorting, states.
// Review and Done live in review.js.

function show(id) {
  document.querySelectorAll(".screen").forEach(function (s) { s.hidden = s.id !== id; });
  document.getElementById("overlay").classList.remove("open");
  document.querySelector(".trace").style.display = id === "s-review" ? "none" : ""; // calm working screen
  window.scrollTo(0, 0);
  var first = document.querySelector("#" + id + " button, #" + id + " input");
  if (first) first.focus();
}
document.addEventListener("click", function (e) {
  var g = e.target.closest("[data-go]"); if (g) show(g.getAttribute("data-go"));
  var st = e.target.closest("[data-state]"); if (st) showState(st.getAttribute("data-state"));
});

// ---- How it works (walkthrough window) ----
var PIP = '<svg width="64" height="56" viewBox="0 0 64 56"><polygon points="8,8 56,8 32,48" fill="#E63946" stroke="#E63946" stroke-width="10" stroke-linejoin="round"/><path d="M24 20 q8 6 16 0" stroke="#fff" stroke-width="3" fill="none"/></svg>';
var ARROW = '<svg width="40" height="20" viewBox="0 0 40 20"><path d="M2 10h32M28 4l6 6-6 6" stroke="#2FD38A" stroke-width="2.5" fill="none" stroke-linecap="round"/></svg>';
var WALK = [
  { t: "Take screenshots like you always do", b: "They land in one folder, Screenshots For Sorting. You don't have to change anything else.",
    a: '<div class="shot"></div><div class="shot"></div>' + ARROW + '<div class="folder">Screenshots<br>For Sorting</div>' },
  { t: "Once a week, I take a look", b: "While you sleep, I go through the new ones on this computer and guess what each one is for. Nothing moves yet.",
    a: PIP + '<span class="mono muted">z z</span><div class="folder">Sunday<br>night</div>' },
  { t: "You check my suggestions", b: "Every screenshot gets one colour, and each colour always means the same thing.",
    a: '<div style="display:flex;flex-direction:column;gap:8px;width:100%;max-width:380px"><div class="chip py">Needs your OK<small>unsure, copies</small></div><div class="chip pr">My suggestions<small>keep, text, or clear</small></div><div class="chip pb">Set aside<small>private, locked</small></div></div>' },
  { t: "Only then do things move", b: "I move only what you approve. When you change one of my suggestions, I learn from it.",
    a: '<div class="folder" style="border-color:#2FD38A">You approve</div>' + ARROW + '<div style="display:flex;flex-direction:column;gap:6px"><div class="folder">Kept</div><div class="folder">To Be Deleted</div></div>' }
];
var w = 0;
function walk() {
  var s = WALK[w];
  document.getElementById("m-step").textContent = "How it works · " + (w + 1) + " of " + WALK.length;
  document.getElementById("m-title").textContent = s.t;
  document.getElementById("m-body").textContent = s.b;
  document.getElementById("m-art").innerHTML = s.a;
  document.getElementById("m-back").hidden = w === 0;
  document.getElementById("m-next").textContent = w === WALK.length - 1 ? "Set up my folder" : "Next";
  [].forEach.call(document.getElementById("m-dots").children, function (d, k) { d.className = k === w ? "on" : ""; });
}
document.getElementById("start").onclick = function () { w = 0; walk(); document.getElementById("overlay").classList.add("open"); document.getElementById("m-next").focus(); };
document.getElementById("m-skip").onclick = function () { show("s-folder"); };
document.getElementById("m-back").onclick = function () { if (w > 0) { w--; walk(); } };
document.getElementById("m-next").onclick = function () { if (w < WALK.length - 1) { w++; walk(); } else show("s-folder"); };
document.addEventListener("keydown", function (e) {
  if (!document.getElementById("overlay").classList.contains("open")) return;
  if (e.key === "Escape") document.getElementById("overlay").classList.remove("open");
  if (e.key === "ArrowRight") document.getElementById("m-next").click();
  if (e.key === "ArrowLeft" && w > 0) document.getElementById("m-back").click();
});

// ---- Sorting (simulated; the real one asks the local server for progress) ----
function lineFor(it) {
  if (it.state === "locked") return ["pb", KIND_COPY[it.kind], "Set aside"];
  if (it.state === "copy") return ["py", "Exact copy of " + it.copy_of + ".", "Needs your OK · copy"];
  if (it.needs_ok) return ["py", it.reason, "Needs your OK · not sure"];
  return ["pr", it.reason, "My suggestion · " + ACTION_WORDS[it.action]];
}
function startSorting() {
  show("s-sorting");
  var items = SAMPLE_REVIEW.items, n = 0, box = document.getElementById("sort-lines");
  box.innerHTML = ""; document.getElementById("sort-review").hidden = true;
  document.getElementById("sort-title").textContent = "Looking at your screenshots";
  document.getElementById("sort-leave").textContent = "Let me know when it's ready";
  (function tick() {
    var it = items[n++], l = lineFor(it), d = document.createElement("div");
    d.className = "line " + l[0];
    d.innerHTML = "<span><span></span><span class='tag'></span></span>";
    d.firstChild.firstChild.textContent = l[1]; d.querySelector(".tag").textContent = l[2];
    box.insertBefore(d, box.firstChild); if (box.children.length > 6) box.removeChild(box.lastChild);
    document.getElementById("sort-count").textContent = n;
    document.getElementById("sort-fill").style.width = Math.round(n / items.length * 100) + "%";
    document.getElementById("sort-eta").textContent = n < items.length ? "About " + Math.max(1, Math.ceil((items.length - n) * 12 / 60)) + " min left" : "Done";
    if (n < items.length) return setTimeout(tick, 1100);
    document.getElementById("sort-eyebrow").textContent = "pip@shift ~ % done";
    document.getElementById("sort-title").textContent = items.length + " screenshots are ready";
    document.getElementById("sort-sub").textContent = "2 need your OK, 5 are my suggestions, 2 are set aside for you. About 3 minutes.";
    document.getElementById("sort-review").hidden = false;
    document.getElementById("sort-leave").textContent = "Do this later";
    document.getElementById("sort-review").focus();
  })();
}
document.getElementById("first-run").onclick = startSorting;
document.getElementById("p-sort").onclick = startSorting;

// ---- Error and empty states (words live in copy.js) ----
function showState(key) {
  var s = STATES[key], el = document.getElementById("s-state");
  var steps = s.steps.length ? "<ol class='steps'>" + s.steps.map(function (x) { return "<li>" + x + "</li>"; }).join("") + "</ol>" : "";
  el.innerHTML = "<div class='narrow' style='display:flex;flex-direction:column;gap:20px;margin-top:40px'>" +
    "<p class='eyebrow'>" + s.eyebrow + "</p><h1>" + s.title + "</h1><p class='sub'>" + s.body + "</p>" + steps +
    "<div class='row'><button class='go' " + (key === "cap" ? "data-review" : "data-go='s-welcome'") + ">" + s.primary + "</button>" +
    (s.secondary ? "<button data-go='s-welcome'>" + s.secondary + "</button>" : "") + "</div></div>";
  show("s-state");
}
