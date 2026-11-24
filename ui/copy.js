// copy.js — every sentence a person reads that is NOT Rick's own words.
// Locked-kind copy is written by people (contract section 3, Raaghavi's lane).
// These are DRAFTS. Space needed: about 17 GB (fresh download on Timo's Mac, Nov 24: 9.5 + 7.5 GB). Download time still to come.

var KIND_COPY = {
  nudity_or_children: "Might show a body or a child. I stopped looking.",
  government_id: "Looks like an ID. I stopped reading.",
  credentials: "Looks like a password. I stopped reading.",
  health_record: "Looks like a health record. I stopped reading.",
  bank_or_payment: "Looks like a bank record. I stopped reading.",
  official_document: "Looks like an official document. I stopped reading.",
  private_message: "Looks like a private message. I stopped reading.",
  contact_details: "Looks like contact details. I stopped reading.",
  marked_confidential: "Marked confidential. I stopped reading.",
  gate_error: "I couldn't check this one, so I locked it to be safe."
};
var KIND_ORDER = ["nudity_or_children", "government_id", "credentials", "health_record",
  "bank_or_payment", "official_document", "private_message", "contact_details",
  "marked_confidential", "gate_error"];

var ACTION_WORDS = { keep_image: "Keep as image", keep_text: "Turn into text", to_be_deleted: "Move to To Be Deleted" };

// Setup step 3. Quick picks so nobody has to write if they don't want to.
var WORK_CHIPS = ["To remember things", "Recipes and ideas", "Receipts and proof",
  "I can't find anything", "Too many copies", "No idea why I took them"];

// Friendly versions of what run.py prints in the terminal. One headline, one line.
var STATES = {
  ollama: { t: "Open the Ollama app", b: "I need it to look at your screenshots. Open it, then try again.", main: "Try again" },
  model:  { t: "One download, once", b: "Rick and Zippy's models are about 17 GB. Use Wi-Fi.", main: "Start download" },
  empty:  { t: "All caught up", b: "Nothing new. I'll look again Sunday night.", main: "Close" },
  cap:    { t: "10 ready, the rest wait", b: "I look at 10 at a time so it never takes long.", main: "Review these 10" }
};
