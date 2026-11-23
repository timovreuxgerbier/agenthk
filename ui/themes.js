// themes.js — seasonal looks for the welcome, sorting and done screens only.
// Rules: never change a buddy's colour (colours carry meaning); never on setup or
// review screens; no costumes for religious holidays; everything still works with
// reduced motion. The first theme whose dates match today wins.

var HANUKKAH_FIRST_NIGHT = ["2026-12-04", "2027-12-24", "2028-12-12", "2029-12-01", "2030-12-20"]; // check yearly

function md(d) { return (d.getMonth() + 1) * 100 + d.getDate(); }           // 10-31 -> 1031
function hanukkahNight(d) {
  for (var i = 0; i < HANUKKAH_FIRST_NIGHT.length; i++) {
    var p = HANUKKAH_FIRST_NIGHT[i].split("-"), start = new Date(+p[0], +p[1] - 1, +p[2]);
    var n = Math.floor((d - start) / 86400000) + 1;
    if (n >= 1 && n <= 8) return n;
  }
  return 0;
}
var HAT = "#2A1F3D", CREAM = "#EDE6D6";
function tint(c) { return "radial-gradient(circle, " + c + " 1.3px, transparent 1.8px)"; }

var THEMES = [
  { id: "hanukkah", name: "Hanukkah", when: function (d) { return hanukkahNight(d) > 0; },
    greet: function (d) { return "Happy Hanukkah · night " + hanukkahNight(d); },
    dots: "#2B3440", acc: null,
    scene: function (d) { return menorah(hanukkahNight(d) || 8); } },
  { id: "halloween", name: "Halloween", when: function (d) { return d.getMonth() === 9; },
    greet: function () { return "Spooky season. Pip sorts in the dark."; }, dots: "#2A2140",
    acc: function () { return "<g transform='translate(0,6)'><ellipse cx='50' cy='6' rx='30' ry='6' fill='" + HAT + "'/>" +
      "<path d='M36 6 L50 -34 Q54 -40 62 -36 L58 -30 L64 6 Z' fill='" + HAT + "'/><rect x='37' y='-3' width='26' height='5' rx='2' fill='#7B5CD6'/></g>"; },
    scene: function () { return "<svg width='60' height='60' viewBox='0 0 60 60' aria-hidden='true'><circle cx='30' cy='30' r='22' fill='#E9E2CF'/><circle cx='40' cy='24' r='20' fill='#030605'/></svg>"; } },
  { id: "muertos", name: "Día de los Muertos", when: function (d) { return md(d) === 1101 || md(d) === 1102; },
    greet: function () { return "Día de los Muertos. Remembering what matters."; }, dots: "#3A2418",
    acc: function () { var f = ""; [28, 39, 50, 61, 72].forEach(function (x, i) {
      f += "<circle cx='" + x + "' cy='" + (i === 2 ? 2 : 5) + "' r='7' fill='" + (i % 2 ? "#C2408A" : "#E8892B") + "'/><circle cx='" + x + "' cy='" + (i === 2 ? 2 : 5) + "' r='2.4' fill='#5A2A10'/>"; });
      return f; },
    scene: function () { return picado(["#C2408A", "#E8892B", "#EDE6D6", "#7B5CD6", "#C2408A", "#E8892B", "#EDE6D6"]); } },
  { id: "winter", name: "Winter holidays", when: function (d) { return md(d) >= 1220 && md(d) <= 1231; },
    greet: function () { return "Cozy season. Pip keeps things tidy."; }, dots: "#22302C",
    acc: function () { return "<path d='M27 12 Q50 -26 73 12 Z' fill='" + CREAM + "'/><rect x='25' y='8' width='50' height='9' rx='4' fill='#B9AE96'/><circle cx='50' cy='-16' r='7' fill='" + CREAM + "'/>"; },
    scene: function () { return snow(); } },
  { id: "newyear", name: "New Year", when: function (d) { return md(d) >= 101 && md(d) <= 107; },
    greet: function () { return "New year, fresh start. Clear last year's screenshots?"; }, dots: "#2E2A1E",
    acc: function () { return "<path d='M37 12 L50 -30 L63 12 Z' fill='" + CREAM + "'/><path d='M41 0 L59 0 M44 -12 L56 -12' stroke='#7B5CD6' stroke-width='4'/><circle cx='50' cy='-32' r='5' fill='#7B5CD6'/>"; },
    scene: function () { return confetti(); } }
];

// ---- small scenes ----
function menorah(n) {
  var s = "<svg width='220' height='88' viewBox='0 0 220 88' role='img' aria-label='Menorah with " + n + " of 8 candles lit'>";
  for (var i = 0; i < 9; i++) {
    var x = 18 + i * 23, center = i === 4, h = center ? 40 : 30, top = 62 - h;
    var rank = [7, 6, 5, 4, -1, 3, 2, 1, 0][i];               // candles are added from the right
    var lit = center || rank < n;
    s += "<rect x='" + (x - 4) + "' y='" + top + "' width='8' height='" + h + "' rx='2' fill='#C9D1DA'/>";
    if (lit) s += "<path class='flame' d='M" + x + " " + (top - 14) + " Q" + (x + 6) + " " + (top - 4) + " " + x + " " + (top - 1) + " Q" + (x - 6) + " " + (top - 4) + " " + x + " " + (top - 14) + " Z' fill='#FFE9B0'/>";
  }
  return s + "<rect x='12' y='62' width='196' height='5' rx='2.5' fill='#C9D1DA'/><rect x='104' y='66' width='12' height='14' fill='#C9D1DA'/><rect x='86' y='80' width='48' height='5' rx='2.5' fill='#C9D1DA'/></svg>";
}
function picado(cols) {
  var s = "<svg width='300' height='54' viewBox='0 0 300 54' aria-hidden='true'><path d='M0 4 Q150 18 300 4' stroke='#8FB3A0' stroke-width='1.5' fill='none'/>";
  cols.forEach(function (c, i) { var x = 12 + i * 41, y = 6 + Math.round(8 * Math.sin(i / 6 * Math.PI));
    s += "<path d='M" + x + " " + y + " h30 v30 l-5 6 l-5 -6 l-5 6 l-5 -6 l-5 6 l-5 -6 Z' fill='" + c + "' opacity='.9'/>"; });
  return s + "</svg>";
}
function snow() { var s = "<svg class='fall' width='300' height='60' viewBox='0 0 300 60' aria-hidden='true'>";
  for (var i = 0; i < 18; i++) s += "<circle cx='" + (i * 17 + 6) + "' cy='" + ((i * 23) % 52 + 4) + "' r='" + (1.5 + (i % 3)) + "' fill='" + CREAM + "' opacity='.75'/>";
  return s + "</svg>"; }
function confetti() { var s = "<svg width='300' height='50' viewBox='0 0 300 50' aria-hidden='true'>", c = ["#EDE6D6", "#7B5CD6", "#B9AE96"];
  for (var i = 0; i < 20; i++) s += "<rect x='" + (i * 15 + 4) + "' y='" + ((i * 19) % 40 + 4) + "' width='6' height='3' rx='1' fill='" + c[i % 3] + "' transform='rotate(" + (i * 37 % 90 - 45) + " " + (i * 15 + 7) + " " + ((i * 19) % 40 + 5) + ")'/>";
  return s + "</svg>"; }

// ---- choose and apply ----
function pickTheme(d) { for (var i = 0; i < THEMES.length; i++) if (THEMES[i].when(d)) return THEMES[i]; return null; }
function applyTheme(id, d) {
  d = d || new Date();
  window.THEME = id === "none" ? null : id && id !== "auto" ? THEMES.filter(function (t) { return t.id === id; })[0] : pickTheme(d);
  var t = window.THEME, win = document.querySelector(".window");
  win.style.backgroundImage = t ? tint(t.dots) + "," + tint(t.dots) : "";
  win.style.backgroundSize = "52px 45px"; win.style.backgroundPosition = "0 0, 26px 22.5px";
  document.getElementById("scene").innerHTML = t ? t.scene(d) : "";
  document.getElementById("greeting").textContent = t ? t.greet(d) : "";
  document.getElementById("welcome-buddies").innerHTML = trio(52);
  document.getElementById("sort-buddies").innerHTML = trio(52);
}
