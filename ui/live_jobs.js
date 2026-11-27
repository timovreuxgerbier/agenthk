// live_jobs.js: Stage 2. The two real jobs, when the page was opened by Shyft's local server.
//   Setup 1 "Get what's missing": downloads the missing model files through Ollama, with progress.
//   Sorting: Rick and Zippy look at the made-up test screenshots (the team's run.py). Nothing is moved.
// One job at a time; Stop works for both. Everything from the server goes on the page as text.
// Stage 2 ends at "Done": run.py saves the trace only, so the review of a real run is Stage 3 (no stale review).
// Prototype (opened as a file): none of this runs; setup.js and flow.js keep their simulations.

function livePost(path, cb) {
  fetch(path, { method: "POST", headers: { "X-Shyft-Key": LIVE.key }, cache: "no-store" })
    .then(function (r) { return r.json().then(function (j) { return r.ok ? j : Promise.reject(j.error || r.status); }); })
    .then(function (j) { cb(j); }, function (why) { cb(null, String(why)); });
}

// Ask "how is the job going?" every second until it isn't running. onTick(job) each time.
function liveFollow(onTick) {
  (function ask() {
    liveGet("/api/job", function (job) {
      if (!job) return onTick({ state: "failed", message: "Lost touch with Shyft's helper. Is its window still open?" });
      onTick(job);
      if (job.state === "running") setTimeout(ask, 1000);
    });
  })();
}

function liveStopButton(id, show) {
  var b = document.getElementById(id);
  if (!b) return;
  b.hidden = !show;
  b.onclick = function () { b.disabled = true; livePost("/api/stop", function () { b.disabled = false; }); };
}

// ---- Setup 1: get the missing model files ----
function liveGetReady() {
  livePost("/api/get-ready", function (job, why) {
    if (!job) { liveNote = why; return renderNeeds(); }
    liveStopButton("need-stop", true);
    liveFollow(function (j) {
      var id = j.buddy === "Zippy" ? "zippy" : j.buddy === "Rick" ? "rick" : null;
      var p = j.gb_total ? Math.min(100, Math.round(j.gb_done / j.gb_total * 100)) : 0;
      if (j.state === "running" && id) {
        have[id] = "downloading"; pct[id] = p;
        liveNote = "Downloading " + j.buddy + "'s model: " + j.gb_done + " of " + j.gb_total + " GB. "
          + "This can take a while. You can leave this open and come back.";
        return renderNeeds();
      }
      if (j.state === "running") return;
      liveStopButton("need-stop", false);
      liveCheck();                                              // the truth, from Ollama itself
      if (j.state !== "done") setTimeout(function () { document.getElementById("need-note").textContent = j.message; }, 300);
    });
  });
}

// ---- Sorting: the made-up test screenshots ----
function liveSort() {
  show("s-sorting");
  var title = document.getElementById("sort-title"), sub = document.getElementById("sort-sub"),
      fill = document.getElementById("sort-fill"), count = document.getElementById("sort-count"),
      notice = document.getElementById("sort-notice"), review = document.getElementById("sort-review");
  review.hidden = true; fill.style.width = "0%"; count.textContent = ""; notice.textContent = "";
  title.textContent = "Getting ready to look";
  sub.textContent = "On this computer, made-up test screenshots only. Nothing is moved, renamed or deleted.";
  document.getElementById("sort-later").textContent = "Back to start";
  livePost("/api/run", function (job, why) {
    if (!job) { title.textContent = "Shyft can't start yet"; sub.textContent = why; return; }
    liveStopButton("sort-stop", true);
    liveFollow(function (j) {
      if (j.notice && j.notice.length && !notice.textContent) notice.textContent = j.notice.join("\n");
      if (j.total) {
        fill.style.width = Math.round((j.zippy_done + j.done) / (2 * j.total) * 100) + "%";
        title.textContent = j.phase === "zippy" ? "Zippy is checking for private screenshots" : "Rick is suggesting what to do";
        count.textContent = "Zippy " + j.zippy_done + " of " + j.total + " · Rick " + j.done + " of " + j.total
          + " · " + Math.floor(j.seconds / 60) + " min " + (j.seconds % 60) + " s";
      }
      if (j.state === "running") return;
      liveStopButton("sort-stop", false);
      title.textContent = j.state === "done" ? "Done" : j.state === "stopped" ? "Stopped" : "The run stopped";
      sub.textContent = j.message;
      document.getElementById("sort-later").textContent = "Later";
      if (j.state === "done") {   // run.py writes the trace only; the review screen for a real run is Stage 3
        fill.style.width = "100%";
        sub.textContent = j.message + " Their suggestions are saved on this computer. Reviewing them here comes in the next stage.";
      }
    });
  });
}
