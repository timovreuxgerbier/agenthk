// start_buddies.js: makes the three buddies on the landing page playful.
// - Eyes follow the pointer (Zippy's eye is closed, so he doesn't).
// - Hover or focus: a face change plus a short reaction (Bloop surprised + tilt, Rick grin + hop, Zippy peeks + nod).
// - Click, tap, Enter or Space: the buddy says its job in a small speech bubble.
// Reduced motion: no eye following and no bouncing; face changes and bubbles still work.
(function () {
  var box = document.getElementById("hero-buddies");
  if (!box) return;
  var still = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  var INKC = "#14172B";
  var WHO = [
    { who: "bloop", name: "Bloop", react: "tilt", says: "I ask before anything moves.",
      face: function (svg, on) { var m = svg.querySelector("ellipse"); if (m) { m.setAttribute("rx", on ? 6.5 : 5); m.setAttribute("ry", on ? 7 : 4.5); } } },
    { who: "pip", name: "Rick", react: "hop", says: "I suggest. You decide.",
      face: function (svg, on) {
        var m = svg.querySelector("path");
        if (m) m.setAttribute("d", on ? "M40 56 Q50 58 60 56 Q60 70 50 70 Q40 70 40 56 Z" : "M43 58 Q50 59 57 58 Q57 66 50 66 Q43 66 43 58 Z");
      } },
    { who: "zippy", name: "Zippy", react: "nod", says: "Private? I stop reading.",
      face: function (svg, on) {   // Zippy keeps his eye closed... except for a quick peek
        var closed = svg.querySelector("path"), peek = svg.querySelector(".peek");
        if (on && !peek) {
          peek = document.createElementNS("http://www.w3.org/2000/svg", "g");
          peek.setAttribute("class", "peek");
          peek.innerHTML = "<circle cx='50' cy='54' r='12' fill='#fff'/><circle cx='50' cy='55' r='5.6' fill='" + INKC + "'/>";
          svg.appendChild(peek);
          if (closed) closed.style.display = "none";
        } else if (!on && peek) { peek.remove(); if (closed) closed.style.display = ""; }
      } }
  ];
  var holders = box.querySelectorAll(".row > span");   // each holds one buddy and its name
  [].forEach.call(holders, function (holder, i) {
    var b = WHO[i], svg = holder.querySelector("svg.buddy");
    if (!b || !svg) return;
    holder.classList.add("pal");
    holder.setAttribute("tabindex", "0");
    holder.setAttribute("role", "button");
    holder.setAttribute("aria-label", b.name + ": " + b.says);
    var bubble = document.createElement("span");
    bubble.className = "bubble"; bubble.setAttribute("aria-hidden", "true"); bubble.textContent = b.says;
    holder.appendChild(bubble);
    var hideTimer;
    function excite(on) { b.face(svg, on); if (on && !still) react(svg, b.react); }
    function speak() {
      excite(true); holder.classList.add("talking");
      clearTimeout(hideTimer);
      hideTimer = setTimeout(function () { holder.classList.remove("talking"); excite(false); }, 2200);
    }
    holder.addEventListener("mouseenter", function () { excite(true); });
    holder.addEventListener("mouseleave", function () { if (!holder.classList.contains("talking")) excite(false); });
    holder.addEventListener("focus", function () { excite(true); });
    holder.addEventListener("blur", function () { if (!holder.classList.contains("talking")) excite(false); });
    holder.addEventListener("click", speak);
    holder.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); speak(); } });
  });

  if (still) return;
  // Eyes follow the pointer: each pupil moves up to 4 units toward it.
  var pending = false, px = 0, py = 0;
  function look() {
    pending = false;
    [].forEach.call(box.querySelectorAll("svg.buddy"), function (svg) {
      var pupil = svg.querySelector(".eye circle:nth-child(2), .peek circle:nth-child(2)");
      if (!pupil) return;
      var r = svg.getBoundingClientRect(), dx = px - (r.left + r.width / 2), dy = py - (r.top + r.height / 2);
      var d = Math.sqrt(dx * dx + dy * dy) || 1, k = Math.min(4, d / 40);
      pupil.setAttribute("transform", "translate(" + (dx / d * k).toFixed(2) + " " + (dy / d * k).toFixed(2) + ")");
    });
  }
  document.addEventListener("pointermove", function (e) {
    px = e.clientX; py = e.clientY;
    if (!pending) { pending = true; requestAnimationFrame(look); }
  });
})();
