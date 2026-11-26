// trust_app.js: the trust ladder inside the app. Two screens:
//   s-trustpick  "How much should Shyft do?" (setup 3 of 4, and "Change step" later)
//   s-trust      the Trust screen: the staircase, where you are, what unlocks the next step
// Plus the ladder walkthrough (one card per step, then the safety net), shown in flow.js's walkthrough window.
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

// ---- The ladder walkthrough ----
function ladderArt(k) {   // six small bars rising; the one being explained is filled; coming ones are dashed
  return "<div class='mini' aria-hidden='true'>" + TRUST_STEPS.map(function (s, i) {
    return "<i class='" + (i === k ? "on" : "") + (s.real ? "" : " soon-bar") + "' style='height:" + (16 + i * 15) + "px'></i>";
  }).join("") + "</div>";
}
function trustDeck(from) {
  var items = TRUST_STEPS.map(function (s, i) {
    return { t: "Step " + (i + 1) + " · " + s.t + (s.real ? "" : " (coming)"),
      b: (s.real ? "Real today. " : TRUST_COMING + " ") + s.walk + (s.up ? " To reach the next step: " + s.up.charAt(0).toLowerCase() + s.up.slice(1) + "." : ""),
      a: function () { return ladderArt(i); } };
  });
  items.push({ t: "The safety net", b: TRUST_ALWAYS + " " + TRUST_BACK + " Climbing the ladder by itself is coming too.",
    a: function () { return buddy("zippy", 60, "idle"); } });
  openDeck({ name: "Trust ladder", items: items, from: from });
}
document.getElementById("tr-walk").onclick = function () { trustDeck("tr-walk"); };
document.getElementById("tp-walk").onclick = function () { trustDeck("tp-walk"); };
