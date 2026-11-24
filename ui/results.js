// results.js: opens the app straight on "ready for you" when it is started after a real run.
// The tester kit opens open_results.html, which comes here as index.html#results.
// The data is the real run (review_data.js, written by dev/make_review.py), so nothing is simulated here.
// Without #results the prototype starts on the welcome screen as before.
(function () {
  if (location.hash !== "#results" || !window.SAMPLE_REVIEW) return;
  var total = SAMPLE_REVIEW.items.length;
  show("s-sorting");
  document.getElementById("sort-fill").style.width = "100%";
  document.getElementById("sort-count").textContent = total + " of " + total;
  document.getElementById("sort-title").textContent = total + " ready for you";
  document.getElementById("sort-sub").textContent =
    "Rick and Zippy just looked at made-up screenshots on this computer. Nothing was moved.";
  document.getElementById("sort-later").textContent = "Later";
  var go = document.getElementById("sort-review");
  go.hidden = false;
  go.focus();
})();
