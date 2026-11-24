// start_buddies.js: the three buddies play at the top of the landing page.
// - They hop in arcs to new spots, one at a time, inside their own area (never over the text or buttons).
// - Touch, click, Enter or Space: the buddy stops, changes face and says its name and its job.
// - Hover or focus: face change. Eyes follow the pointer (Zippy's eye is closed unless he peeks).
// - "Pause buddies" stops the hopping (anything that moves by itself needs a pause, WCAG 2.2.2).
// - Reduced motion: they stand still in a row; faces and lines still work.
(function () {
  var area = document.getElementById("hero-buddies");
  if (!area) return;
  var still = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  var INKC = "#14172B";
  var WHO = [
    { who: "bloop", name: "Bloop", react: "tilt",
      says: "I'm Bloop. When Rick isn't sure, I ask you first. Nothing moves without your OK.",
      face: function (svg, on) { var m = svg.querySelector("ellipse"); if (m) { m.setAttribute("rx", on ? 6.5 : 5); m.setAttribute("ry", on ? 7 : 4.5); } } },
    { who: "pip", name: "Rick", react: "hop",
      says: "I'm Rick. I suggest what to do with each screenshot. You decide.",
      face: function (svg, on) {
        var m = svg.querySelector("path");
        if (m) m.setAttribute("d", on ? "M40 56 Q50 58 60 56 Q60 70 50 70 Q40 70 40 56 Z" : "M43 58 Q50 59 57 58 Q57 66 50 66 Q43 66 43 58 Z");
      } },
    { who: "zippy", name: "Zippy", react: "nod",
      says: "I'm Zippy. If a screenshot looks private, I lock it and stop reading.",
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

  // ---- Build the play area ----
  var small = window.innerWidth < 640;
  var SIZE = small ? 64 : 92;
  area.innerHTML = "";
  area.classList.add("play");
  if (still) area.classList.add("still");
  var pals = WHO.map(function (b) {
    var holder = document.createElement("div");
    holder.className = "pal";
    holder.setAttribute("tabindex", "0");
    holder.setAttribute("role", "button");
    holder.setAttribute("aria-label", b.says);
    holder.innerHTML = buddy(b.who, b.who === "pip" ? Math.round(SIZE * 1.2) : SIZE, "themed") +
      "<span class='nm'>" + b.name + "</span><span class='bubble' aria-hidden='true'>" + b.says + "</span>";
    area.appendChild(holder);
    return { b: b, el: holder, svg: holder.querySelector("svg.buddy"), x: 0, busy: false, talking: false, timer: null };
  });

  function excite(p, on) { p.b.face(p.svg, on); if (on && !still) react(p.svg, p.b.react); }
  function speak(p) {
    pals.forEach(function (o) { if (o !== p && o.talking) { clearTimeout(o.timer); quiet(o); } });  // one voice at a time
    excite(p, true); p.talking = true; p.el.classList.add("talking");
    var bub = p.el.querySelector(".bubble"); bub.style.marginLeft = "0px"; bub.style.setProperty("--tail", "0px");   // keep the bubble on screen
    var r = bub.getBoundingClientRect(), edge = 10, shift = 0;
    if (r.left < edge) shift = edge - r.left; else if (r.right > window.innerWidth - edge) shift = window.innerWidth - edge - r.right;
    bub.style.marginLeft = Math.round(shift) + "px";
    bub.style.setProperty("--tail", Math.round(-shift) + "px");   // the pointer still points at the buddy
    clearTimeout(p.timer);
    p.timer = setTimeout(function () { quiet(p); }, 3600);
  }
  function quiet(p) { p.talking = false; p.el.classList.remove("talking"); excite(p, false); }
  pals.forEach(function (p) {
    var el = p.el;
    el.addEventListener("mouseenter", function () { p.hover = true; excite(p, true); });
    el.addEventListener("mouseleave", function () { p.hover = false; if (!p.talking) excite(p, false); });
    el.addEventListener("focus", function () { p.hover = true; excite(p, true); });
    el.addEventListener("blur", function () { p.hover = false; if (!p.talking) excite(p, false); });
    el.addEventListener("click", function () { speak(p); });
    el.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); speak(p); } });
  });

  // ---- Where each buddy stands ----
  function widthOf(p) { return p.el.offsetWidth; }
  function place(p, x) { p.x = x; p.el.style.transform = "translateX(" + Math.round(x) + "px)"; }
  function home() {   // left, middle, right
    var W = area.clientWidth;
    place(pals[0], W * 0.22 - widthOf(pals[0]) / 2);
    place(pals[1], W * 0.5 - widthOf(pals[1]) / 2);
    place(pals[2], W * 0.78 - widthOf(pals[2]) / 2);
  }
  home();
  window.addEventListener("resize", function () { if (!hopping) home(); });
  if (still) return;

  // ---- Hopping ----
  var paused = false, hopping = false;
  var pause = document.createElement("button");
  pause.type = "button"; pause.className = "quiet pause-buddies";
  pause.textContent = "Pause buddies";
  pause.setAttribute("aria-pressed", "false");
  area.parentNode.insertBefore(pause, area.nextSibling);
  pause.onclick = function () {
    paused = !paused;
    pause.textContent = paused ? "Let them play" : "Pause buddies";
    pause.setAttribute("aria-pressed", String(paused));
  };

  function freeSpot(p) {   // a new x that keeps clear of the other two
    var W = area.clientWidth, w = widthOf(p);
    for (var i = 0; i < 12; i++) {
      var x = Math.random() * Math.max(0, W - w);
      if (Math.abs(x - p.x) < w * 0.6) continue;   // a real jump, not a shuffle
      var ok = pals.every(function (o) { return o === p || Math.abs(o.x - x) > (widthOf(o) + w) / 2 + 8; });
      if (ok) return x;
    }
    return null;
  }
  function arc(p, x0, x1, high, ms) {   // one jump from x0 to x1, squash on take-off and landing
    p.busy = true; hopping = true;
    var anim = p.el.animate([
      { transform: "translate(" + x0 + "px,0) scale(1.06,.9)" },
      { transform: "translate(" + (x0 + (x1 - x0) * 0.5) + "px,-" + high + "px) scale(.96,1.05)", offset: 0.5 },
      { transform: "translate(" + x1 + "px,0) scale(1.08,.88)", offset: 0.9 },
      { transform: "translate(" + x1 + "px,0) scale(1,1)" }
    ], { duration: ms, easing: "ease-in-out" });
    p.x = x1;   // others keep clear of the landing spot straight away
    anim.onfinish = function () { place(p, x1); p.busy = false; hopping = pals.some(function (o) { return o.busy; }); };
  }
  function free(p) { return !p.talking && !p.hover && !p.busy; }
  function hop() {
    if (paused || document.hidden) return;
    var ready = pals.filter(free);
    if (!ready.length) return;
    var p = ready[Math.floor(Math.random() * ready.length)], x1 = freeSpot(p);
    if (x1 !== null && Math.random() < 0.6) {
      return arc(p, p.x, x1, 50 + Math.random() * 40, 650 + Math.abs(x1 - p.x) * 0.6);
    }
    // No room, or just for fun: swap places with the nearest free buddy. One leaps high, the other hops under.
    var others = pals.filter(function (o) { return o !== p && free(o); })
      .sort(function (a, b) { return Math.abs(a.x - p.x) - Math.abs(b.x - p.x); });
    if (!others.length) return;
    var o = others[0], xp = p.x, xo = o.x, ms = 700 + Math.abs(xp - xo) * 0.5;
    arc(p, xp, xo + (widthOf(o) - widthOf(p)) / 2, 110 + Math.random() * 30, ms);
    arc(o, xo, xp + (widthOf(p) - widthOf(o)) / 2, 26, ms);
  }
  setInterval(hop, 1800);

  // ---- Eyes follow the pointer (up to 4 units) ----
  var pending = false, px = 0, py = 0;
  function look() {
    pending = false;
    pals.forEach(function (p) {
      var pupil = p.svg.querySelector(".eye circle:nth-child(2), .peek circle:nth-child(2)");
      if (!pupil) return;
      var r = p.svg.getBoundingClientRect(), dx = px - (r.left + r.width / 2), dy = py - (r.top + r.height / 2);
      var d = Math.sqrt(dx * dx + dy * dy) || 1, k = Math.min(4, d / 40);
      pupil.setAttribute("transform", "translate(" + (dx / d * k).toFixed(2) + " " + (dy / d * k).toFixed(2) + ")");
    });
  }
  document.addEventListener("pointermove", function (e) {
    px = e.clientX; py = e.clientY;
    if (!pending) { pending = true; requestAnimationFrame(look); }
  });
})();
