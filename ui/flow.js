// flow.js — moving between screens: welcome, How it works, setup, sorting, states.
// Review and Done live in review.js.

function show(id) {
  document.querySelectorAll(".screen").forEach(function (s) { s.hidden = s.id !== id; });
  document.getElementById("overlay").classList.remove("open");
  document.getElementById("trace").style.display = id === "s-welcome" ? "" : "none"; // decoration on welcome only
  var main = document.querySelector("#" + id + " .main:not([hidden])");
  if (main) main.focus();
}
document.addEventListener("click", function (e) {
  var g = e.target.closest("[data-go]"); if (g) show(g.getAttribute("data-go"));
  var st = e.target.closest("[data-state]"); if (st) showState(st.getAttribute("data-state"));
});

// Prototype menu: hidden while presenting. Press P to show or hide.
document.addEventListener("keydown", function (e) {
  if ((e.key === "p" || e.key === "P") && !/INPUT|TEXTAREA/.test(document.activeElement.tagName)) {
    var p = document.getElementById("proto"); p.hidden = !p.hidden;
    document.body.classList.toggle("proto-on", !p.hidden);
  }
});

// ---- Welcome + setup content ----
applyTheme("auto");
// Prototype: preview any theme. Hanukkah previews the chosen night (2026 dates).
function previewTheme() {
  var id = document.getElementById("theme-pick").value, n = +document.getElementById("theme-night").value || 1;
  applyTheme(id, id === "hanukkah" ? new Date(2026, 11, 3 + n) : undefined);
}
document.getElementById("theme-pick").onchange = previewTheme;
document.getElementById("theme-night").oninput = previewTheme;
document.getElementById("chips").innerHTML = WORK_CHIPS.map(function (c) {
  return "<button type='button' aria-pressed='false'>" + c + "</button>";
}).join("");
document.getElementById("chips").onclick = function (e) {
  var b = e.target.closest("button"); if (b) b.setAttribute("aria-pressed", b.getAttribute("aria-pressed") !== "true");
};
document.getElementById("voice").onclick = function () {
  document.getElementById("voice-note").textContent = "Prototype only: voice notes aren't built yet.";
};
document.getElementById("start").onclick = function () { show("s-need"); };

// ---- How it works: the longer explanations live here ----
var WALK = [
  { t: "Screenshots go to one folder", b: "Take them like you always do. They land in Screenshots For Sorting, the only folder Rick looks at.",
    a: function () { return '<div class="folder">Screenshots<br>For Sorting</div>'; } },
  { t: "Rick looks while you sleep", b: "Every Sunday night, on this computer, Rick guesses what each new screenshot is for. Nothing moves yet.",
    a: function () { return buddy("pip", 64, "idle"); } },
  { t: "One colour, one meaning", b: "Yellow needs your OK. Red is Rick's suggestion. Blue is private: Zippy stops reading and locks it.",
    a: function () { return buddy("bloop", 48, "idle b1") + buddy("pip", 56, "idle b2") + buddy("zippy", 48, "idle b3"); } },
  { t: "You decide, nothing is deleted", b: "Only what you approve moves. Cleared files go to a To Be Deleted folder that you empty yourself.",
    a: function () { return '<div class="folder">Kept</div><div class="folder">To Be Deleted</div>'; } }
];
var w = 0;
function walk() {
  var s = WALK[w];
  document.getElementById("m-step").textContent = "How it works · " + (w + 1) + " of " + WALK.length;
  document.getElementById("m-title").textContent = s.t;
  document.getElementById("m-body").textContent = s.b;
  document.getElementById("m-art").innerHTML = s.a();
  document.getElementById("m-back").hidden = w === 0;
  document.getElementById("m-next").textContent = w === WALK.length - 1 ? "Got it" : "Next";
  document.getElementById("m-dots").innerHTML = WALK.map(function (_, k) { return "<i" + (k === w ? " class='on'" : "") + "></i>"; }).join("");
}
function closeWalk() { document.getElementById("overlay").classList.remove("open"); document.getElementById("how").focus(); }
document.getElementById("how").onclick = function () { w = 0; walk(); document.getElementById("overlay").classList.add("open"); document.getElementById("m-next").focus(); };
document.getElementById("m-close").onclick = closeWalk;
document.getElementById("m-back").onclick = function () { if (w > 0) { w--; walk(); } };
document.getElementById("m-next").onclick = function () { if (w < WALK.length - 1) { w++; walk(); } else closeWalk(); };
document.addEventListener("keydown", function (e) {
  if (!document.getElementById("overlay").classList.contains("open")) return;
  if (e.key === "Escape") closeWalk();
  if (e.key === "ArrowRight") document.getElementById("m-next").click();
  if (e.key === "ArrowLeft" && w > 0) document.getElementById("m-back").click();
});

// ---- Sorting (simulated; the real one will ask the local server for progress) ----
function startSorting() {
  show("s-sorting");
  var total = SAMPLE_REVIEW.items.length, n = 0;
  document.getElementById("sort-review").hidden = true;
  document.getElementById("sort-title").textContent = "Looking at your screenshots";
  document.getElementById("sort-sub").textContent = "On this computer. Nothing moves yet.";
  document.getElementById("sort-later").textContent = "Tell me when it's ready";
  (function tick() {
    n++;
    document.getElementById("sort-fill").style.width = Math.round(n / total * 100) + "%";
    document.getElementById("sort-count").textContent = n + " of " + total;
    if (n < total) return setTimeout(tick, 900);
    document.getElementById("sort-title").textContent = total + " ready for you";
    document.getElementById("sort-sub").textContent = "About 3 minutes to review.";
    document.getElementById("sort-later").textContent = "Later";
    document.getElementById("sort-review").hidden = false;
    document.getElementById("sort-review").focus();
    react(document.querySelector("#sort-buddies .b2"), "hop");
  })();
}
document.getElementById("finish").onclick = startSorting;
document.getElementById("p-sort").onclick = startSorting;

// ---- Error and empty states: one headline, one line, one button ----
function showState(key) {
  var s = STATES[key];
  document.getElementById("s-state").innerHTML = "<div class='body'>" + buddy(key === "empty" ? "pip" : "bloop", 60, "idle") +
    "<h1>" + s.t + "</h1><p class='sub'>" + s.b + "</p><button class='main' " +
    (key === "cap" ? "data-review" : "data-go='s-welcome'") + ">" + s.main + "</button>" +
    (key === "empty" ? "" : "<button class='quiet' data-go='s-welcome'>Later</button>") + "</div>";
  show("s-state");
}
