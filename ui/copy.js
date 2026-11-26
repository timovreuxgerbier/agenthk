// copy.js — every sentence a person reads that is NOT Rick's own words.
// Locked-kind copy is written by people (contract section 3, Raaghavi's lane).
// These are DRAFTS. Download: 11.2 GB (gemma4:e4b 6.6 + gemma4:e2b 4.6, as measured for the Windows kit).
// Decision D27 (Nov 25): the same two builds everywhere (gemma4:e4b-it-q4_K_M, gemma4:e2b-it-q4_K_M). Timo's 17 GB
// on Nov 24 was the Mac's short-name builds, which Shyft no longer uses.
// Free disk needed: 18 GB (the download plus room to work). Download time still to come.

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
  model:  { t: "One download, once", b: "Rick and Zippy's models are an 11.2 GB download. Use Wi-Fi.", main: "Start download" },
  empty:  { t: "All caught up", b: "Nothing new. I'll look again Sunday night.", main: "Close" },
  cap:    { t: "10 ready, the rest wait", b: "I look at 10 at a time so it never takes long.", main: "Review these 10" }
};
