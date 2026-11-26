// mode.js: light or dark, for the app (index.html) and the landing page (start.html).
// Follows the computer's own setting until the person picks one with the switch; that choice is remembered
// in this browser. Load it in <head> so the page never flashes the wrong colours.
(function () {
  var KEY = "shyft-theme", buttons = [];
  function saved() { try { var v = localStorage.getItem(KEY); return v === "light" || v === "dark" ? v : null; } catch (e) { return null; } }
  function system() { return window.matchMedia && matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark"; }
  function apply(v) { document.documentElement.setAttribute("data-theme", v); label(); }
  function label() {
    var now = document.documentElement.getAttribute("data-theme");
    buttons.forEach(function (b) {
      b.textContent = now === "light" ? "Dark mode" : "Light mode";
      b.setAttribute("aria-label", "Switch to " + (now === "light" ? "dark" : "light") + " mode");
    });
  }
  apply(saved() || system());
  if (window.matchMedia) {   // if the computer switches (for example at sunset), follow it, unless the person chose
    var mq = matchMedia("(prefers-color-scheme: light)"), follow = function () { if (!saved()) apply(system()); };
    if (mq.addEventListener) mq.addEventListener("change", follow); else if (mq.addListener) mq.addListener(follow);
  }
  // modeButton(button): turns a button into the light/dark switch (the manual override).
  window.modeButton = function (b) {
    buttons.push(b);
    b.onclick = function () {
      var v = document.documentElement.getAttribute("data-theme") === "light" ? "dark" : "light";
      try { localStorage.setItem(KEY, v); } catch (e) {}
      apply(v);
    };
    label();
  };
})();
