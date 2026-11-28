// trust.js: the trust ladder. Shyft earns more of your computer, one step at a time.
// The six steps live ONLY here, so the app and the landing page always say the same thing (and match the deck, slide 8).
// Used by: setup (pick where to start), the Trust screen, and the landing page (start.html).
// Prototype: the chosen step is remembered in this browser only. Climbing and dropping back are coming too.

// real: built today (Shyft names files; you review; apply.py moves what you approved, writes a receipt, and can undo).
// Steps without real: true are COMING and say so on every screen.
var TRUST_STEPS = [
  { t: "Suggests names only", b: "Rick suggests a clear name for each screenshot. Nothing moves.", up: "After 50 suggestions reviewed", real: true,
    walk: "Rick looks at each new screenshot and suggests a clear name. Nothing moves, nothing is renamed. You just see the suggestions." },
  { t: "Moves after your OK", b: "You review, Shyft applies, you get a receipt and can undo.", up: "4 in 5 accepted unchanged", real: true,
    walk: "You review each suggestion. Shyft applies only what you approved, writes a receipt of every move, and can undo any of it." },
  { t: "Downloads and Desktop", b: "Looks there too. Still asks first.", up: "2 weeks, nothing undone",
    walk: "Shyft also looks at screenshots in Downloads and on the Desktop. It still asks before anything moves." },
  { t: "Runs overnight", b: "On a schedule, while you sleep. Still asks first.", up: "30 days, no wrong move undone",
    walk: "Shyft looks at new screenshots on a schedule, overnight, so suggestions are ready in the morning. It still asks first." },
  { t: "Moves on its own", b: "In folders you chose. You can undo any move.", up: "Receipts someone can check",
    walk: "Shyft moves screenshots on its own, only into folders you chose, and keeps receipts so you can undo any move." },
  { t: "Approved for work files", b: "Your workplace approves it for client work.", locked: true,
    walk: "Your workplace checks the receipts and approves Shyft for client work. Only they can unlock this step." }
];
var TRUST_ALWAYS = "Always: nothing leaves your computer, nothing is deleted, the code is open.";
var TRUST_BACK = "Coming: Shyft goes back one step if you undo a wrong move, or a private file gets past Zippy.";
var TRUST_COMING = "Coming: not built yet.";
var TRUST_RISKY = {   // shown before starting high up the ladder, and must be confirmed
  4: "Starting at Step 4 means Shyft looks at your screenshots overnight from day one, before it has learned how you work.",
  5: "Starting at Step 5 means Shyft moves files on its own from day one, before it has made a single suggestion you approved."
};
var TRUST_SAFE = "Zippy still locks private files, you can undo any move, and Shyft drops back a step if it gets one wrong.";

function trustMax() { var m = 1; TRUST_STEPS.forEach(function (s, i) { if (s.real) m = i + 1; }); return m; }   // highest step that is built
function trustGet() { var n = 1; try { n = +localStorage.getItem("shyft-trust") || 1; } catch (e) {} return Math.min(trustMax(), Math.max(1, n)); }
function trustSet(n) { try { localStorage.setItem("shyft-trust", String(n)); } catch (e) {} }

// The staircase: six cards rising left to right, with what unlocks each next step. here = the current step (0 for none).
function trustStairs(el, here) {
  el.innerHTML = "<ol class='stairs'>" + TRUST_STEPS.map(function (s, i) {
    var n = i + 1, cls = (n === here ? " here" : "") + (s.real ? "" : " coming");
    return "<li class='stair" + cls + "' style='--rise:" + i + "'>" +
      (i > 0 ? "<span class='unlock'>" + TRUST_STEPS[i - 1].up + "</span>" : "") +
      "<div class='card'>" + (n === here ? "<span class='you'>You are here</span>" : "") +
      "<b>Step " + n + (s.real ? "" : " <em class='soon'>Coming</em>") + "</b><strong>" + s.t + "</strong><span>" + s.b + "</span></div></li>";
  }).join("") + "</ol>";
}

// The picker (setup, and "Change step"): a radio list, Step 1 recommended. Only built steps can be picked.
// Starting at Step 4 or 5 will need a warning plus a tick-box (ready for when those steps are built). onChange(step, ready) tells the page
// whether its main button may continue.
function trustPicker(el, start, onChange) {
  el.innerHTML = "<fieldset class='pick'><legend class='small'>Start at</legend>" + TRUST_STEPS.map(function (s, i) {
    var n = i + 1;
    var off = !s.real;   // coming steps can't be picked yet
    return "<label class='pick-row" + (off ? " locked" : "") + "'>" +
      "<input type='radio' name='trust' value='" + n + "'" + (n === start ? " checked" : "") + (off ? " disabled" : "") + ">" +
      "<span class='num'>" + n + "</span><span class='what'><strong>" + s.t + (n === 1 ? " <em class='rec'>Recommended</em>" : "") +
      (off ? " <em class='soon'>Coming</em>" : "") + "</strong>" +
      "<span>" + (s.locked ? "Needs your workplace to approve it." : off ? s.b + " Not built yet." : s.b) + "</span></span></label>";
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
