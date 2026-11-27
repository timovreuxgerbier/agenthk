// live.js: talks to Shyft's local server (app/shyft_app.py) when the page was opened by it.
// Opened as a plain file (the prototype), LIVE is false and every screen works as before.
// The server puts a secret key in the address (?k=...); every question to it carries that key.
// Rule: anything that comes from the server (model names, graphics names, sizes) goes onto the page
// as text (textContent), never as markup, so a strange name can never become part of the page.

var LIVE = (function () {
  var m = /[?&]k=([A-Za-z0-9_-]+)/.exec(location.search);
  return location.protocol === "http:" && location.hostname === "127.0.0.1" && m ? { key: m[1] } : false;
})();

// Ask the server. cb(answer) on success, cb(null, why) if it couldn't answer.
function liveGet(path, cb) {
  fetch(path, { headers: { "X-Shyft-Key": LIVE.key }, cache: "no-store" })
    .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
    .then(function (j) { cb(j); }, function (why) { cb(null, why); });
}

// A small helper: an element with a class and text (never markup).
function liveEl(tag, cls, text) {
  var e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}

// The Spec screen: the numbers from shyft_requirements.json, and what this computer has.
// "Enough" comes from the server's own judgement (s.meets), the same one Setup uses.
function liveSpec(s) {
  var r = s.requirements, c = s.computer;
  [].forEach.call(document.querySelectorAll("[data-req]"), function (e) {
    var k = e.getAttribute("data-req");
    if (k === "memory") e.textContent = r.memory_gb + " GB";
    if (k === "disk") e.textContent = r.free_disk_gb + " GB (" + r.download_gb + " GB download)";
    if (k === "disk-short") e.textContent = r.free_disk_gb + " GB";
  });
  function row(label, value, ok) {   // a word next to every mark: colour is never the only signal
    var li = liveEl("li"), span = liveEl("span", null, value);
    li.appendChild(liveEl("b", null, label));
    if (ok === true || ok === false) {
      span.appendChild(document.createTextNode(" · "));
      span.appendChild(liveEl("span", ok ? "ok" : "miss", ok ? "✓ Enough" : "Not enough"));
    }
    li.appendChild(span);
    return li;
  }
  var yours = document.getElementById("spec-yours");
  yours.textContent = "";
  var head = liveEl("li", "yours-title"); head.appendChild(liveEl("b", null, "This computer")); head.appendChild(liveEl("span", null, "checked just now, nothing changed"));
  yours.appendChild(head);
  yours.appendChild(row("Memory", c.memory_gb == null ? "couldn't check" : c.memory_gb + " GB", s.meets.memory));
  yours.appendChild(row("Free disk", c.free_disk_gb == null ? "couldn't check" : c.free_disk_gb + " GB free, " + r.need_now_gb + " GB needed now", s.meets.disk));
  yours.appendChild(row("Graphics", c.graphics ? c.graphics.join(", ") : "couldn't check", null));
  yours.hidden = false;
  document.getElementById("spec-below").textContent = s.meets.memory === false
    ? "Below the minimum isn't promised. You can still try, and we'd like to know how it goes." : "";
}

// The review screen: the newest real review, found by Shyft's own records (stage 0.3), not a file in ui/.
// No review yet: the screens keep the made-up sample and say "Sample data".
function liveReview() {
  liveGet("/api/review", function (review) {
    if (!review || !review.items) return;
    window.SAMPLE_REVIEW = review;
    window.SAMPLE_PREVIEWS = {};          // pictures come in a later stage; until then no picture, never a wrong one
    window.REVIEW_SOURCE = "Real run";
  });
}
if (LIVE) liveReview();
