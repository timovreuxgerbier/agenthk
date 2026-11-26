// locked.js: the Locked folder screen. DESIGN ONLY: nothing here is built yet, and the screen says so.
// It lists the screenshots Zippy locked in the current review data, with the same plain reasons as the review.
// Wording rule: never say "encrypted" (or "secure vault"): that is not built. "Locked" means Zippy stopped reading.

function openLocked(from) {
  var items = SAMPLE_REVIEW.items.filter(function (it) { return it.state === "locked"; });
  var back = from || "s-welcome";
  document.getElementById("s-locked").innerHTML =
    "<div class='body'>" +
      "<span class='design-only'>Design only · not built yet</span>" +
      "<div class='row' style='gap:14px'>" + buddy("zippy", 54, "idle") + "<h1>Locked folder</h1></div>" +
      "<p class='sub'>Zippy locked these because they looked private, and Shyft stopped reading them. They stay on this computer.</p>" +
      (items.length ? "<ul class='locklist'>" + items.map(function (it) {
        return "<li><span class='thumb' aria-hidden='true'>&#128274;</span><span class='what'><b>" + esc(KIND_COPY[it.kind] || KIND_COPY.gate_error) +
          "</b><span>" + esc(it.file) + (it.file_date ? " · " + esc(it.file_date) : "") + "</span></span>" +
          "<button class='lk-try'>Look</button><button class='lk-try'>Not private</button></li>";
      }).join("") + "</ul>" : "<p class='small'>Nothing is locked right now.</p>") +
      "<p class='small' id='lk-note' aria-live='polite'></p>" +
    "</div>" +
    "<div class='foot'><button data-go='" + back + "'>Back</button><span class='spacer'></span><button class='main' data-go='" + back + "'>Done</button></div>";
  [].forEach.call(document.querySelectorAll("#s-locked .lk-try"), function (b) {
    b.onclick = function () { document.getElementById("lk-note").textContent = "Design only: these buttons aren't built yet."; };
  });
  show("s-locked");
}
document.getElementById("p-locked").onclick = function () { openLocked(current === "s-locked" ? "s-welcome" : current); };
