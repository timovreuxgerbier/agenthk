// buddies.js — Bloop (yellow, needs your OK), Pip (red, suggestions), Zippy (blue, locked).
// They blink and bob by themselves; react() plays a short one-off reaction.
// All motion stops when the computer is set to reduce motion (see styles.css).

function buddy(who, size, extra) {
  var s = size || 56, c = extra || "";
  if (who === "pip") return '<svg class="buddy ' + c + '" width="' + s + '" height="' + Math.round(s * .88) + '" viewBox="0 0 64 56" aria-hidden="true">' +
    '<polygon points="8,8 56,8 32,48" fill="#E63946" stroke="#E63946" stroke-width="10" stroke-linejoin="round"/>' +
    '<circle class="eye" cx="32" cy="20" r="5" fill="#fff"/></svg>';
  var fill = who === "bloop" ? "#F7C531" : "#2F7BEA", eye = who === "bloop" ? "#3A2F10" : "#0B1A33";
  return '<svg class="buddy ' + c + '" width="' + s + '" height="' + Math.round(s * .9) + '" viewBox="0 0 64 58" aria-hidden="true">' +
    '<polygon points="32,8 56,50 8,50" fill="' + fill + '" stroke="' + fill + '" stroke-width="10" stroke-linejoin="round"/>' +
    '<circle class="eye" cx="26" cy="36" r="3.4" fill="' + eye + '"/><circle class="eye" cx="38" cy="36" r="3.4" fill="' + eye + '"/></svg>';
}

// The three together, gently bobbing (welcome, sorting, done).
function trio(size) {
  return '<span class="row" style="gap:16px;align-items:flex-end">' + buddy("bloop", size, "idle b1") +
    buddy("pip", Math.round(size * 1.2), "idle b2") + buddy("zippy", size, "idle b3") + '</span>';
}

// One short reaction: "hop" (approved), "nod" (locked), "tilt" (needs your OK).
function react(el, how) {
  if (!el) return;
  el.classList.remove("hop", "nod", "tilt");
  void el.getBoundingClientRect(); // restart the animation
  el.classList.add(how);
  el.addEventListener("animationend", function () { el.classList.remove(how); }, { once: true });
}
