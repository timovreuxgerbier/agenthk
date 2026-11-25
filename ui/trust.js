// trust.js: the trust ladder. Shyft earns more of your computer, one step at a time.
// The six steps live ONLY here, so the app and the landing page always say the same thing (and match the deck, slide 8).
// Used by: setup (pick where to start), the Trust screen, and the landing page (start.html).
// Prototype: the chosen step is remembered in this browser only. Climbing and dropping back are not tracked yet.

var TRUST_STEPS = [
  { t: "Suggests only", b: "In one test folder. Nothing moves.", up: "After 50 suggestions reviewed" },
  { t: "Moves after your OK", b: "Renames and sorts, once you say yes.", up: "4 in 5 accepted unchanged" },
  { t: "Downloads and Desktop", b: "Looks there too. Still asks first.", up: "2 weeks, nothing undone" },
  { t: "Runs overnight", b: "On a schedule, while you sleep. Still asks first.", up: "30 days, no wrong move undone" },
  { t: "Moves on its own", b: "In folders you chose. You can undo any move.", up: "Receipts someone can check" },
  { t: "Approved for work files", b: "Your workplace approves it for client work.", locked: true }
];
var TRUST_ALWAYS = "Always: nothing leaves your computer, nothing is deleted, the code is open.";
var TRUST_BACK = "Shyft goes back one step if you undo a wrong move, or a private file gets past Zippy.";
var TRUST_RISKY = {   // shown before starting high up the ladder, and must be confirmed
  4: "Starting at Step 4 means Shyft looks at your screenshots overnight from day one, before it has learned how you work.",
  5: "Starting at Step 5 means Shyft moves files on its own from day one, before it has made a single suggestion you approved."
};
var TRUST_SAFE = "Zippy still locks private files, you can undo any move, and Shyft drops back a step if it gets one wrong.";

function trustGet() { var n = 1; try { n = +localStorage.getItem("shyft-trust") || 1; } catch (e) {} return Math.min(5, Math.max(1, n)); }
function trustSet(n) { try { localStorage.setItem("shyft-trust", String(n)); } catch (e) {} }

// The staircase: six cards rising left to right, with what unlocks each next step. here = the current step (0 for none).
function trustStairs(el, here) {
  el.innerHTML = "<ol class='stairs'>" + TRUST_STEPS.map(function (s, i) {
    var n = i + 1, cls = (n === here ? " here" : "") + (s.locked ? " locked" : "");
    return "<li class='stair" + cls + "' style='--rise:" + i + "'>" +
      (i > 0 ? "<span class='unlock'>" + TRUST_STEPS[i - 1].up + "</span>" : "") +
      "<div class='card'>" + (n === here ? "<span class='you'>You are here</span>" : "") +
      "<b>Step " + n + "</b><strong>" + s.t + "</strong><span>" + s.b + "</span></div></li>";
  }).join("") + "</ol>";
}

// The picker (setup, and "Change step"): a radio list, Step 1 recommended, Step 6 locked,
// and a warning plus a tick-box before starting at Step 4 or 5. onChange(step, ready) tells the page
// whether its main button may continue.
function trustPicker(el, start, onChange) {
  el.innerHTML = "<fieldset class='pick'><legend class='small'>Start at</legend>" + TRUST_STEPS.map(function (s, i) {
    var n = i + 1;
    return "<label class='pick-row" + (s.locked ? " locked" : "") + "'>" +
      "<input type='radio' name='trust' value='" + n + "'" + (n === start ? " checked" : "") + (s.locked ? " disabled" : "") + ">" +
      "<span class='num'>" + n + "</span><span class='what'><strong>" + s.t + (n === 1 ? " <em class='rec'>Recommended</em>" : "") + "</strong>" +
      "<span>" + (s.locked ? "Needs your workplace to approve it. You can't skip to this one." : s.b) + "</span></span></label>";
  }).join("") + "</fieldset>" +
    "<div class='risk' id='trust-risk' hidden><p id='trust-risk-text'></p><p class='small'>" + TRUST_SAFE + "</p>" +
    "<label class='ok-row'><input type='checkbox' id='trust-ok'> I understand. Start here.</label></div>" +
    "<p class='small always'>" + TRUST_BACK + "</p>";
  var risk = el.querySelector("#trust-risk"), ok = el.querySelector("#trust-ok");
  function update() {
    var n = +el.querySelector("input[name=trust]:checked").value, risky = !!TRUST_RISKY[n];
    risk.hidden = !risky;
    if (risky) { el.querySelector("#trust-risk-text").textContent = TRUST_RISKY[n]; }
    onChange(n, !risky || ok.checked);
  }
  el.addEventListener("change", function (e) { if (e.target.name === "trust") ok.checked = false; update(); });
  update();
}
