// sample_review.js — FAKE data in the exact shape of review_contract.md v0.2.
// No real screenshots. When the real agent is connected, review.json replaces this.
// It is a .js file (not .json) so the page also works when opened by double-click.

var SAMPLE_REVIEW = {
  contract: "0.2", run_id: "20261117-210000", made: "2026-11-17T21:04:10",
  counts: { total: 9, open: 6, locked: 2, copies: 1 },
  items: [
    { id: "a1", file: "Screenshot (41).png", file_date: "2026-11-09", state: "open", kind: "none",
      action: "keep_text", new_name: "bogota-flight-dec-18",
      reason: "A flight confirmation with a date, time and booking reference.",
      why_saved: "Probably kept to check your flight time (a guess).", confidence: 0.93, needs_ok: false, copy_of: null },
    { id: "a2", file: "Screenshot (42).png", file_date: "2026-11-10", state: "open", kind: "none",
      action: "keep_image", new_name: "arepas-recipe",
      reason: "A recipe card for arepas with a photo and ingredient list.",
      why_saved: "Probably saved to cook later (a guess).", confidence: 0.88, needs_ok: false, copy_of: null },
    { id: "a3", file: "Screenshot (43).png", file_date: "2026-11-11", state: "open", kind: "none",
      action: "to_be_deleted", new_name: null,
      reason: "A capture of an empty desktop with no text or content.",
      why_saved: "Probably taken by accident (a guess).", confidence: 0.9, needs_ok: false, copy_of: null },
    { id: "a4", file: "Screenshot (44).png", file_date: "2026-11-12", state: "open", kind: "none",
      action: "keep_image", new_name: "whiteboard-notes",
      reason: "A blurry photo of a whiteboard. I can't read most of it.",
      why_saved: "Maybe notes from class (a guess).", confidence: 0.41, needs_ok: true, copy_of: null },
    { id: "a5", file: "Screenshot (45).png", file_date: "2026-11-13", state: "open", kind: "none",
      action: "keep_text", new_name: "dentist-thu-14-nov",
      reason: "An appointment reminder: dentist, Thursday 14 November, 3:30 pm.",
      why_saved: "Probably kept so you don't forget the appointment (a guess).", confidence: 0.9, needs_ok: false, copy_of: null },
    { id: "a6", file: "Screenshot (46).png", file_date: "2026-11-14", state: "open", kind: "none",
      action: "keep_text", new_name: "syllabus-week-12",
      reason: "A course syllabus page listing the week 12 readings.",
      why_saved: "Probably kept to find the readings later (a guess).", confidence: 0.86, needs_ok: false, copy_of: null },
    { id: "c1", file: "Screenshot (47).png", file_date: "2026-11-14", state: "copy", kind: "none",
      action: "to_be_deleted", new_name: null, reason: null, why_saved: null,
      confidence: 1.0, needs_ok: false, copy_of: "Screenshot (41).png" },
    { id: "l1", file: "Screenshot (48).png", file_date: "2026-11-15", state: "locked", kind: "bank_or_payment",
      action: null, new_name: null, reason: null, why_saved: null, confidence: 0.99, needs_ok: true, copy_of: null },
    { id: "l2", file: "Screenshot (49).png", file_date: "2026-11-16", state: "locked", kind: "gate_error",
      action: null, new_name: null, reason: null, why_saved: null, confidence: null, needs_ok: true, copy_of: null }
  ]
};

// PROTOTYPE ONLY: a few words standing in for the screenshot image itself.
// The real page shows the actual image, served by our local server.
var SAMPLE_PREVIEWS = {
  a1: ["Messages · Avianca", "Your flight AV 245 to Bogotá is confirmed. Dec 18, departs 7:45 AM."],
  a2: ["Instagram · @cocina", "Arepas de queso: 2 cups masarepa, 1 cup cheese, warm water, salt."],
  a3: ["Desktop", "(nothing on screen)"],
  a4: ["Photos", "(blurry whiteboard: a few arrows and the word 'deadline')"],
  a5: ["Calendar", "Dentist · Thu 14 Nov · 3:30 pm · 5th Ave Dental"],
  a6: ["Canvas · PSDS 5330", "Week 12 readings: Bainbridge (1983); Lee and See (2004)."],
  c1: ["Messages · Avianca", "Your flight AV 245 to Bogotá is confirmed. Dec 18, departs 7:45 AM."],
  l1: ["(hidden)", "(hidden)"], l2: ["(hidden)", "(hidden)"]
};
