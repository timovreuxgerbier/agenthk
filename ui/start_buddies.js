// start_buddies.js: the three buddies as little monsters at the top of the landing page.
// - Horns grow from their dots: Bloop 2, Zippy 1, Rick 2. Cream horns, so body colours (and meanings) stay the same.
// - Monster moves, one at a time: waddle-walk to a new spot, stomp (the others wobble), roar (mouth open, fangs).
// - Touch, click, Enter or Space: the buddy stops and says its name and its job.
// - Hover or focus: face change. Eyes follow the pointer (Zippy's eye is closed unless he peeks).
// - "Pause buddies" stops the moving (anything that moves by itself needs a pause, WCAG 2.2.2).
// - Reduced motion: they stand still in a row; horns, faces and lines still work.
// Landing page only: the app keeps the calm buddies.
(function () {
  var area = document.getElementById("hero-buddies");
  if (!area) return;
  var still = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  var INKC = "#14172B", TONGUE = "#FF7A9C";
  var NS = "http://www.w3.org/2000/svg";
  var COLOR = { bloop: "#F7C531", pip: "#E63946", zippy: "#2F7BEA" };
  // Horns in the buddy's own colour, drawn behind the body so the bases tuck in. Each: [base left, base right, tip].
  var HORNS = {
    bloop: [[[33, 24], [49, 13], [25, -10]], [[67, 24], [51, 13], [75, -10]]],
    zippy: [[[40, 20], [60, 20], [50, -15]]],
    pip:   [[[22, 17], [36, 10], [11, -13]], [[78, 17], [64, 10], [89, -13]]]
  };
  var MOUTH = {   // normal, happy (hover), roar
    bloop: null,   // Bloop's mouth is an ellipse: changed by size below
    pip: ["M43 58 Q50 59 57 58 Q57 66 50 66 Q43 66 43 58 Z", "M40 56 Q50 58 60 56 Q60 70 50 70 Q40 70 40 56 Z",
          "M37 54 Q50 57 63 54 Q63 76 50 76 Q37 76 37 54 Z"],
    zippy: ["M43 76 Q50 82 57 76", "M41 75 Q50 84 59 75", "M40 73 Q50 90 60 73 Z"]
  };
  var WHO = [
    { who: "bloop", name: "Bloop", says: "I'm Bloop. When Rick isn't sure, I ask you first. Nothing moves without your OK." },
    { who: "pip", name: "Rick", says: "I'm Rick. I suggest what to do with each screenshot. You decide." },
    { who: "zippy", name: "Zippy", says: "I'm Zippy. If a screenshot looks private, I lock it and stop reading." }
  ];

  function el(tag, attrs) { var e = document.createElementNS(NS, tag); for (var k in attrs) e.setAttribute(k, attrs[k]); return e; }
  function monsterize(svg, who) {
    [].forEach.call(svg.querySelectorAll("circle"), function (c) { if (+c.getAttribute("cy") < 0) c.remove(); });  // dots become horns
    var first = svg.firstChild;
    HORNS[who].forEach(function (h) {
      var L = h[0], R = h[1], T = h[2], g = el("g", { "class": "horn" });
      var mx = (L[0] + R[0]) / 2, my = (L[1] + R[1]) / 2;
      // a slightly curved cone: the sides bow a little toward the outside
      var cx = mx + (T[0] - mx) * 0.55 + (L[0] - R[0]) * 0.18, cy = my + (T[1] - my) * 0.55;
      g.appendChild(el("path", { d: "M" + L + " Q" + cx + "," + cy + " " + T + " L" + R + " Z", fill: COLOR[who],
        stroke: COLOR[who], "stroke-width": "3", "stroke-linejoin": "round" }));
      [0.28, 0.5, 0.7].forEach(function (t) {   // three little black ridges across the horn
        var px = mx + (T[0] - mx) * t, py = my + (T[1] - my) * t, half = (1 - t) * 0.42;
        var dx = (R[0] - L[0]) * half, dy = (R[1] - L[1]) * half;
        g.appendChild(el("line", { x1: px - dx, y1: py - dy, x2: px + dx, y2: py + dy, stroke: INKC, "stroke-width": "2.2", "stroke-linecap": "round" }));
      });
      svg.insertBefore(g, first);
    });
  }
  function facePaths(svg) { return [].filter.call(svg.querySelectorAll("path"), function (x) { return !x.closest(".horn, .fangs, .silly"); }); }
  function mouthOf(svg) { var f = facePaths(svg); return f[f.length - 1]; }
  // Faces: 0 normal, 1 happy or curious (hover, talking), 2 roar
  function face(p, mood) {
    var svg = p.svg, who = p.b.who;
    [].forEach.call(svg.querySelectorAll(".fangs, .silly"), function (x) { x.remove(); });
    var eyeG = svg.querySelector(".eye"); if (eyeG) eyeG.style.display = "";
    var peekG = svg.querySelector(".peek"); if (peekG) peekG.style.display = "";
    if (who === "bloop") {
      var m = svg.querySelector("ellipse");
      m.setAttribute("rx", [5, 6.5, 8][mood]); m.setAttribute("ry", [4.5, 7, 9][mood]); m.setAttribute("cy", mood === 2 ? 80 : 79);
      if (mood === 2) addFangs(svg, 80 - 8, 50);
    }
    if (who === "pip") {
      mouthOf(svg).setAttribute("d", MOUTH.pip[mood]);
      if (mood === 2) addFangs(svg, 54.5, 50);
    }
    if (who === "zippy") {   // calm guard: his eye peeks open when curious or roaring
      var paths = facePaths(svg);
      var closed = paths[0], mouth = paths[1], peek = svg.querySelector(".peek");
      mouth.setAttribute("d", MOUTH.zippy[mood]);
      mouth.setAttribute("fill", mood === 2 ? INKC : "none");
      if (mood > 0 && !peek) {
        peek = el("g", { "class": "peek" });
        peek.innerHTML = "<circle cx='50' cy='54' r='12' fill='#fff'/><circle cx='50' cy='55' r='5.6' fill='" + INKC + "'/>";
        svg.appendChild(peek); closed.style.display = "none";
      } else if (mood === 0 && peek) { peek.remove(); closed.style.display = ""; }
      if (mood === 2) addFangs(svg, 73.5, 50);
    }
  }
  // Silly faces, on top of the happy face. Eye centre: Rick 38, the others 54.
  function silly(p, kind) {
    face(p, 1);
    var svg = p.svg, who = p.b.who, ey = who === "pip" ? 38 : 54;
    var eye = who === "zippy" ? svg.querySelector(".peek") : svg.querySelector(".eye");
    var mouthBottom = { bloop: 84, pip: 69, zippy: 80 }[who];
    var g = el("g", { "class": "silly" });
    if (kind === "tongue") {
      g.innerHTML = "<path d='M44 " + (mouthBottom - 3) + " Q44 " + (mouthBottom + 10) + " 50 " + (mouthBottom + 10) + " Q56 " + (mouthBottom + 10) + " 56 " + (mouthBottom - 3) + " Z' fill='" + TONGUE + "' stroke='" + INKC + "' stroke-width='2'/>" +
        "<line x1='50' y1='" + (mouthBottom - 1) + "' x2='50' y2='" + (mouthBottom + 5) + "' stroke='" + INKC + "' stroke-width='1.6' stroke-linecap='round'/>";
    } else if (kind === "squint") {   // eye squeezed shut, like ^
      if (eye) eye.style.display = "none";
      g.innerHTML = "<path d='M39 " + (ey + 4) + " L50 " + (ey - 6) + " L61 " + (ey + 4) + "' fill='none' stroke='" + INKC + "' stroke-width='5' stroke-linecap='round' stroke-linejoin='round'/>";
    } else if (kind === "dizzy") {    // a spinning spiral instead of the pupil
      if (eye) { var pu = eye.querySelector("circle:nth-child(2)"); if (pu) pu.style.display = "none"; }
      var pts = [];   // a clean spiral: the radius grows with the angle
      for (var a = 0; a <= Math.PI * 4; a += 0.25) { var r = 0.7 + a * 0.75; pts.push((50 + r * Math.cos(a)).toFixed(1) + " " + (ey + r * Math.sin(a)).toFixed(1)); }
      g.innerHTML = "<g class='spin' style='transform-box:fill-box;transform-origin:center'><path d='M" + pts.join(" L") + "' fill='none' stroke='" + INKC + "' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'/></g>";
      setTimeout(function () { if (eye) { var pu2 = eye.querySelector("circle:nth-child(2)"); if (pu2) pu2.style.display = ""; } }, 1500);
    } else if (kind === "googly") {   // the eye pops big
      if (eye) eye.style.display = "none";
      g.innerHTML = "<circle cx='50' cy='" + ey + "' r='18.5' fill='#fff' stroke='" + INKC + "' stroke-width='1.5'/><circle cx='53' cy='" + (ey + 3) + "' r='7.5' fill='" + INKC + "'/>";
    }
    svg.appendChild(g);
  }
  function addFangs(svg, top, cx) {   // two little white fangs hanging from the top of an open mouth
    var g = el("g", { "class": "fangs" });
    g.innerHTML = "<path d='M" + (cx - 7) + " " + top + " L" + (cx - 4) + " " + (top + 5) + " L" + (cx - 1) + " " + top + " Z' fill='#fff'/>" +
                  "<path d='M" + (cx + 1) + " " + top + " L" + (cx + 4) + " " + (top + 5) + " L" + (cx + 7) + " " + top + " Z' fill='#fff'/>";
    svg.appendChild(g);
  }

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
    holder.innerHTML = "<span class='body'>" + buddy(b.who, b.who === "pip" ? Math.round(SIZE * 1.2) : SIZE, "") + "</span>" +
      "<span class='nm'>" + b.name + "</span><span class='bubble' aria-hidden='true'>" + b.says + "</span>";
    area.appendChild(holder);
    var p = { b: b, el: holder, body: holder.querySelector(".body"), svg: holder.querySelector("svg.buddy"), x: 0, busy: false, talking: false, timer: null };
    monsterize(p.svg, b.who);
    return p;
  });

  function once(target, cls, ms) {   // play a CSS move once
    target.classList.remove(cls); void target.getBoundingClientRect(); target.classList.add(cls);
    setTimeout(function () { target.classList.remove(cls); }, ms);
  }
  function speak(p) {
    pals.forEach(function (o) { if (o !== p && o.talking) { clearTimeout(o.timer); quiet(o); } });  // one voice at a time
    face(p, 1); p.talking = true; p.el.classList.add("talking");
    var bub = p.el.querySelector(".bubble"); bub.style.marginLeft = "0px"; bub.style.setProperty("--tail", "0px");
    var r = bub.getBoundingClientRect(), edge = 10, shift = 0;   // keep the bubble on screen
    if (r.left < edge) shift = edge - r.left; else if (r.right > window.innerWidth - edge) shift = window.innerWidth - edge - r.right;
    bub.style.marginLeft = Math.round(shift) + "px";
    bub.style.setProperty("--tail", Math.round(-shift) + "px");   // the pointer still points at the buddy
    if (!still) once(p.body, "wiggle", 500);
    clearTimeout(p.timer);
    p.timer = setTimeout(function () { quiet(p); }, 3800);
  }
  function quiet(p) { p.talking = false; p.el.classList.remove("talking"); face(p, 0); }
  pals.forEach(function (p) {
    var h = p.el;
    h.addEventListener("mouseenter", function () { p.hover = true; if (!p.busy) face(p, 1); });
    h.addEventListener("mouseleave", function () { p.hover = false; if (!p.talking && !p.busy) face(p, 0); });
    h.addEventListener("focus", function () { p.hover = true; face(p, 1); });
    h.addEventListener("blur", function () { p.hover = false; if (!p.talking) face(p, 0); });
    h.addEventListener("click", function () { speak(p); });
    h.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); speak(p); } });
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
  var paused = false, walking = false;
  window.addEventListener("resize", function () { if (!walking) home(); });
  if (still) return;

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

  // ---- Monster moves ----
  function free(p) { return !p.talking && !p.hover && !p.busy; }
  function walk(p) {   // waddle to a new spot; may pass in front of the others
    var W = area.clientWidth, w = widthOf(p), x1 = null;
    for (var i = 0; i < 12 && x1 === null; i++) {
      var x = Math.random() * Math.max(0, W - w);
      var clear = pals.every(function (o) { return o === p || Math.abs(o.x - x) > (widthOf(o) + w) / 2 + 8; });
      if (Math.abs(x - p.x) > w * 0.5 && clear) x1 = x;
    }
    if (x1 === null) return false;
    var x0 = p.x, ms = Math.max(1400, Math.abs(x1 - x0) / 85 * 1000);   // slow and heavy: about 85 px a second
    p.busy = true; walking = true; p.el.classList.add("walking");
    p.body.classList.add("waddle");
    var anim = p.el.animate([{ transform: "translateX(" + x0 + "px)" }, { transform: "translateX(" + x1 + "px)" }],
      { duration: ms, easing: "linear" });
    p.x = x1;   // others keep clear of the spot straight away
    anim.onfinish = function () {
      place(p, x1); p.body.classList.remove("waddle"); p.el.classList.remove("walking");
      once(p.body, "stomp", 420);   // a heavy last step
      p.busy = false; walking = pals.some(function (o) { return o.busy; });
    };
    return true;
  }
  function stomp(p) {   // big stomp: the ground shakes and the others wobble
    p.busy = true;
    once(p.body, "stomp-big", 700);
    setTimeout(function () { pals.forEach(function (o) { if (o !== p && !o.talking) once(o.body, "wobble", 500); }); }, 260);
    setTimeout(function () { p.busy = false; }, 760);
  }
  function roar(p) {   // mouth wide open, fangs, a shake
    p.busy = true; face(p, 2); once(p.body, "roar", 900);
    setTimeout(function () { if (!p.talking) face(p, p.hover ? 1 : 0); p.busy = false; }, 950);
  }
  function goofy(p) {   // a silly face for a moment
    var kinds = ["tongue", "squint", "dizzy", "googly"];
    p.busy = true; silly(p, kinds[Math.floor(Math.random() * kinds.length)]); once(p.body, "wiggle", 500);
    setTimeout(function () { if (!p.talking) face(p, p.hover ? 1 : 0); p.busy = false; }, 1500);
  }
  function act() {
    if (paused || document.hidden) return;
    var ready = pals.filter(free);
    if (!ready.length) return;
    var p = ready[Math.floor(Math.random() * ready.length)], dice = Math.random();
    if (dice < 0.45) { if (!walk(p)) goofy(p); }
    else if (dice < 0.62) stomp(p);
    else if (dice < 0.77) roar(p);
    else goofy(p);
  }
  setInterval(act, 2200);

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
