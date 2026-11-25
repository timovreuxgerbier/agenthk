// trust_app.js: the trust ladder inside the app. Two screens:
//   s-trustpick  "How much should Shyft do?" (setup 3 of 4, and "Change step" later)
//   s-trust      the Trust screen: the staircase, where you are, what unlocks the next step
// The steps themselves live in trust.js.

var trustReturn = "s-welcome", trustMode = "setup", trustChoice = 1;

function openTrust(from) {
  if (from) trustReturn = from;
  trustStairs(document.getElementById("trust-stairs"), trustGet());
  show("s-trust");
}

function openPicker(mode) {   // mode: "setup" (during setup) or "change" (from the Trust screen)
  trustMode = mode;
  var main = document.getElementById("tp-main");
  document.getElementById("tp-eyebrow").textContent = mode === "setup" ? "Setup 3 of 4" : "Trust ladder";
  trustPicker(document.getElementById("trust-pick"), trustGet(), function (n, ready) {
    trustChoice = n;
    main.disabled = !ready;
    main.textContent = mode === "change" ? "Save" : n >= 4 ? "Start at Step " + n : "Continue";
  });
  show("s-trustpick");
}

document.getElementById("folder-next").onclick = function () { openPicker("setup"); };
document.getElementById("tp-back").onclick = function () { if (trustMode === "setup") show("s-folder"); else openTrust(); };
document.getElementById("tp-main").onclick = function () {
  trustSet(trustChoice);
  if (trustMode === "setup") show("s-work"); else openTrust();
};
document.getElementById("work-back").onclick = function () { openPicker("setup"); };
document.getElementById("tr-change").onclick = function () { openPicker("change"); };
document.getElementById("tr-done").onclick = function () { show(trustReturn); };
document.getElementById("trust-always").textContent = TRUST_ALWAYS;
document.getElementById("trust-back").textContent = TRUST_BACK;
// Prototype menu
document.getElementById("p-trustpick").onclick = function () { openPicker("setup"); };
document.getElementById("p-trust").onclick = function () { openTrust(current === "s-trust" ? null : current); };
