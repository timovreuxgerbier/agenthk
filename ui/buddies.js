// buddies.js — Bloop (yellow, needs your OK), Rick (red, suggestions), Zippy (blue, locked).
// Art follows the brand file (WebsiteTriangles): soft triangles, big eyes, small mouths.
// Themes (themes.js) may add an accessory on top. They NEVER change a buddy's colour,
// because each colour carries one meaning in the app.

var BODY = { pip: "#E63946", bloop: "#F7C531", zippy: "#2F7BEA" };
var INK = "#14172B";

function face(who) {
  if (who === "zippy") return "<path d='M37 55 Q50 64 63 55' fill='none' stroke='" + INK + "' stroke-width='4.5' stroke-linecap='round'/>" +
    "<path d='M43 76 Q50 82 57 76' fill='none' stroke='" + INK + "' stroke-width='4' stroke-linecap='round'/>";
  var mouth = who === "pip" ? "<path d='M42 75 Q50 76 58 75 Q58 85 50 85 Q42 85 42 75 Z' fill='" + INK + "'/>"
                            : "<ellipse cx='50' cy='79' rx='5' ry='4.5' fill='" + INK + "'/>";
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
    "<polygon points='50,28 78,74 22,74' fill='" + BODY[who] + "' stroke='" + BODY[who] + "' stroke-width='34' stroke-linejoin='round'/>" +
    face(who) + acc + "</svg>";
}

// The three together, gently bobbing (welcome, sorting, done).
function trio(size) {
  return "<span class='row' style='gap:" + Math.round(size * .45) + "px;align-items:flex-end'>" + buddy("bloop", size, "idle b1 themed") +
    buddy("pip", Math.round(size * 1.2), "idle b2 themed") + buddy("zippy", size, "idle b3 themed") + "</span>";
}

// One short reaction: "hop" (approved), "nod" (locked), "tilt" (needs your OK).
function react(el, how) {
  if (!el) return;
  el.classList.remove("hop", "nod", "tilt");
  void el.getBoundingClientRect(); // restart the animation
  el.classList.add(how);
  el.addEventListener("animationend", function () { el.classList.remove(how); }, { once: true });
}
