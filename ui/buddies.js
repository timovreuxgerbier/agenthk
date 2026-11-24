// buddies.js — Bloop (yellow, needs your OK), Rick (red, suggestions), Zippy (blue, locked).
// Art follows the brand file (WebsiteTriangles): soft triangles, big eyes, small mouths.
// Themes (themes.js) may add an accessory on top. They NEVER change a buddy's colour,
// because each colour carries one meaning in the app.

var BODY = { pip: "#E63946", bloop: "#F7C531", zippy: "#2F7BEA" };
var INK = "#14172B";

function face(who) {
  if (who === "zippy") return "<path d='M37 55 Q50 64 63 55' fill='none' stroke='" + INK + "' stroke-width='4.5' stroke-linecap='round'/>" +
    "<path d='M43 76 Q50 82 57 76' fill='none' stroke='" + INK + "' stroke-width='4' stroke-linecap='round'/>";
  if (who === "pip")   // Rick points down (like the logo), so his face sits higher, in the wide part
    return "<g class='eye'><circle cx='50' cy='38' r='13.5' fill='#fff'/><circle cx='50' cy='39' r='6.2' fill='" + INK + "'/></g>" +
      "<path d='M43 58 Q50 59 57 58 Q57 66 50 66 Q43 66 43 58 Z' fill='" + INK + "'/>";
  var mouth = "<ellipse cx='50' cy='79' rx='5' ry='4.5' fill='" + INK + "'/>";
  return "<g class='eye'><circle cx='50' cy='54' r='13.5' fill='#fff'/><circle cx='50' cy='55' r='6.2' fill='" + INK + "'/></g>" + mouth;
}
function marks(who) {
  var c = BODY[who];
  if (who === "zippy") return "<circle cx='50' cy='-4' r='4.2' fill='" + c + "'/>";
  if (who === "bloop") return "<circle cx='38' cy='-1' r='3.8' fill='" + c + "'/><circle cx='62' cy='-1' r='3.8' fill='" + c + "'/>";
  return "";
}
function buddy(who, size, extra) {
  var s = size || 56, acc = window.THEME && THEME.acc && /themed/.test(extra || "") ? THEME.acc(who) : "";
  return "<svg class='buddy " + (extra || "") + "' width='" + s + "' height='" + s + "' viewBox='0 0 100 100' style='overflow:visible' aria-hidden='true'>" +
    (acc ? "" : marks(who)) +
    "<polygon points='" + (who === "pip" ? "22,26 78,26 50,72" : "50,28 78,74 22,74") + "' fill='" + BODY[who] + "' stroke='" + BODY[who] + "' stroke-width='34' stroke-linejoin='round'/>" +
    face(who) + acc + "</svg>";
}

// The three together, gently bobbing (welcome, sorting, done). named=true adds each name underneath,
// for the places where people first meet them.
var NAMES = { bloop: "Bloop", pip: "Rick", zippy: "Zippy" };
function trio(size, named) {
  function one(who, s, cls) {
    var svg = buddy(who, s, cls);
    return named ? "<span style='display:inline-flex;flex-direction:column;align-items:center;gap:6px'>" + svg +
      "<span class='small' style='font-weight:600'>" + NAMES[who] + "</span></span>" : svg;
  }
  return "<span class='row' style='gap:" + Math.round(size * .45) + "px;align-items:flex-end'>" + one("bloop", size, "idle b1 themed") +
    one("pip", Math.round(size * 1.2), "idle b2 themed") + one("zippy", size, "idle b3 themed") + "</span>";
}

// One short reaction: "hop" (approved), "nod" (locked), "tilt" (needs your OK).
function react(el, how) {
  if (!el) return;
  el.classList.remove("hop", "nod", "tilt");
  void el.getBoundingClientRect(); // restart the animation
  el.classList.add(how);
  el.addEventListener("animationend", function () { el.classList.remove(how); }, { once: true });
}
