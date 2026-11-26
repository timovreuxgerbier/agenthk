// live.js: talks to Shyft's local server (app/shyft_app.py) when the page was opened by it.
// Opened as a plain file (the prototype), LIVE is false and every screen works as before.
// The server puts a secret key in the address (?k=...); every question to it carries that key.

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

// The Spec screen: the numbers from shyft_requirements.json, and what this computer has.
function liveSpec(s) {
  var r = s.requirements, c = s.computer;
  [].forEach.call(document.querySelectorAll("[data-req]"), function (el) {
    var k = el.getAttribute("data-req");
    if (k === "memory") el.textContent = r.memory_gb + " GB";
    if (k === "disk") el.textContent = r.free_disk_gb + " GB (" + r.download_gb + " GB download)";
    if (k === "disk-short") el.textContent = r.free_disk_gb + " GB";
  });
  function line(label, value, ok) {   // a word next to every mark: colour is never the only signal
    var mark = ok === true ? "<span class='ok'>✓ Meets the minimum</span>" : ok === false ? "<span class='miss'>Below the minimum</span>" : "";
    return "<li><b>" + label + "</b><span>" + value + (mark ? " · " + mark : "") + "</span></li>";
  }
  var yours = document.getElementById("spec-yours");
  yours.innerHTML = "<li class='yours-title'><b>This computer</b><span>checked just now, nothing changed</span></li>" +
    line("Memory", c.memory_gb == null ? "couldn't check" : c.memory_gb + " GB", s.meets.memory) +
    line("Free disk", c.free_disk_gb == null ? "couldn't check" : c.free_disk_gb + " GB", c.free_disk_gb == null ? null : c.free_disk_gb >= r.free_disk_gb) +
    line("Graphics", c.graphics ? c.graphics.join(", ") : "couldn't check", null);
  yours.hidden = false;
  var below = document.getElementById("spec-below");
  below.textContent = s.meets.memory === false ? "Below the minimum isn't promised. You can still try, and we'd like to know how it goes." : "";
}
