// flow.js — moving between screens: welcome, How it works, setup, sorting, states.
// Review and Done live in review.js.

var current = "s-welcome", returnTo = "s-welcome";   // where to go back to after an error screen
function show(id) {
  if (id === "s-state" && current !== "s-state") returnTo = current;
  current = id;
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

// Light or dark (mode.js): the switch in the title bar.
modeButton(document.getElementById("mode"));
// Projector mode: bigger everything. Press B (or the prototype menu).
function toggleBig() { document.body.classList.toggle("big"); }
document.getElementById("p-big").onclick = toggleBig;
// Prototype menu: hidden while presenting. Press P to show or hide.
document.addEventListener("keydown", function (e) {
  if ((e.key === "b" || e.key === "B") && !/INPUT|TEXTAREA/.test(document.activeElement.tagName)) toggleBig();
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
document.getElementById("start").onclick = function () {   // the spec screen comes first
  show("s-spec");
  if (window.LIVE) liveGet("/api/status", function (s) { if (s) liveSpec(s); });   // real numbers and "This computer"
};
document.getElementById("spec-next").onclick = function () { show("s-need"); if (window.LIVE) liveCheck(); };

// ---- How it works: the longer explanations live here ----
var WALK = [
  { t: "Screenshots go to one folder", b: "Take them like you always do. They land in Screenshots For Sorting, the only folder Rick looks at.",
    a: function () { return '<div class="folder">Screenshots<br>For Sorting</div>'; } },
  { t: "Rick looks while you sleep", b: "Every Sunday night, on this computer, Rick guesses what each new screenshot is for. Nothing moves yet.",
    a: function () { return buddy("pip", 64, "idle"); } },
  { t: "Meet Bloop, Rick and Zippy", b: "Rick suggests what to do with each screenshot. Bloop (yellow) asks for your OK when Rick isn't sure. Zippy (blue) locks private ones and stops reading.",
    a: function () { return trio(46, true); } },
  { t: "You decide, nothing is deleted", b: "At first, only what you approve moves. Shyft earns more one step at a time, and you can undo any move. Cleared files go to a To Be Deleted folder that you empty yourself.",
    a: function () { return '<div class="folder">Kept</div><div class="folder">To Be Deleted</div>'; } }
];
// One walkthrough window for every walkthrough: How it works, and the trust ladder (trust_app.js).
// A deck is { name, items: [{ t, b, a }], from: id of the button to return focus to }.
var deck = { name: "How it works", items: WALK, from: "how" }, w = 0;
function walk() {
  var s = deck.items[w];
  document.getElementById("m-step").textContent = deck.name + " · " + (w + 1) + " of " + deck.items.length;
  document.getElementById("m-title").textContent = s.t;
  document.getElementById("m-body").textContent = s.b;
  document.getElementById("m-art").innerHTML = s.a();
  document.getElementById("m-back").hidden = w === 0;
  document.getElementById("m-next").textContent = w === deck.items.length - 1 ? "Got it" : "Next";
  document.getElementById("m-dots").innerHTML = deck.items.map(function (_, k) { return "<i" + (k === w ? " class='on'" : "") + "></i>"; }).join("");
}
function openDeck(d) { deck = d; w = 0; walk(); document.getElementById("overlay").classList.add("open"); document.getElementById("m-next").focus(); }
function closeWalk() { document.getElementById("overlay").classList.remove("open"); var f = document.getElementById(deck.from); if (f) f.focus(); }
document.getElementById("how").onclick = function () { openDeck({ name: "How it works", items: WALK, from: "how" }); };
document.getElementById("m-close").onclick = closeWalk;
document.getElementById("m-back").onclick = function () { if (w > 0) { w--; walk(); } };
document.getElementById("m-next").onclick = function () { if (w < deck.items.length - 1) { w++; walk(); } else closeWalk(); };
document.addEventListener("keydown", function (e) {
  if (!document.getElementById("overlay").classList.contains("open")) return;
  if (e.key === "Escape") closeWalk();
  if (e.key === "ArrowRight") document.getElementById("m-next").click();
  if (e.key === "ArrowLeft" && w > 0) document.getElementById("m-back").click();
});

// ---- Sorting (prototype: simulated. Live: the real run, in live_jobs.js) ----
function startSorting() {
  if (window.LIVE) return liveSort();
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

// ---- Error and empty states: one headline, one line, one button. No dead ends:
// "Try again" really re-checks Ollama and returns the person to where they were;
// "Start download" goes to Step 1 with the download running.
function showState(key) {
  if (current !== "s-state") returnTo = current;   // record it BEFORE the Back button is built
  var s = STATES[key], back = key === "ollama" ? "<button class='quiet' data-go='" + returnTo + "'>Back</button>" : "";
  document.getElementById("s-state").innerHTML = "<div class='body'>" + buddy(key === "empty" ? "pip" : "bloop", 60, "idle") +
    "<h1>" + s.t + "</h1><p class='sub'>" + s.b + "</p><button class='main' id='st-main'" + (key === "cap" ? " data-review" : "") + ">" + s.main + "</button>" +
    "<p class='small' id='st-note' aria-live='polite'></p>" +
    (key === "ollama" ? "<button class='quiet protoonly' id='st-pretend'>Prototype: pretend Ollama is open</button>" : "") +
    (key === "empty" || key === "cap" ? "" : back || "<button class='quiet' data-go='s-welcome'>Later</button>") + "</div>";
  var m = document.getElementById("st-main");
  if (key === "empty") m.onclick = function () { show("s-welcome"); };
  if (key === "model") m.onclick = function () { show("s-need"); setScenario("models"); getMissing(); };
  if (key === "ollama") {
    m.onclick = function () {
      document.getElementById("st-note").textContent = "Checking…";
      ollamaRunning(function (ok) {
        if (ok) return show(returnTo);
        document.getElementById("st-note").textContent = "Still can't reach Ollama. Is it open? Look for its icon at the top of your screen.";
      });
    };
    document.getElementById("st-pretend").onclick = function () { show(returnTo); };
  }
  show("s-state");
}
