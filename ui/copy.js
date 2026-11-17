// copy.js — every sentence a person reads that is NOT Pip's own words.
// Contract section 3: locked-kind copy is written by people (Raaghavi's lane).
// These are DRAFTS for her to replace. The model never writes these.

var KIND_COPY = {
  nudity_or_children: "Might show a person's body or a child. I stopped looking.",
  government_id: "Looks like an ID document. I stopped reading it.",
  credentials: "Looks like a password or login. I stopped reading it.",
  health_record: "Looks like a health record. I stopped reading it.",
  bank_or_payment: "Looks like a bank or payment record. I stopped reading it.",
  official_document: "Looks like an official document. I stopped reading it.",
  private_message: "Looks like a private message. I stopped reading it.",
  contact_details: "Looks like someone's contact details. I stopped reading it.",
  marked_confidential: "Says it's confidential. I stopped reading it.",
  gate_error: "I couldn't check this one properly, so I locked it to be safe."
};

// Ladder order (contract D23): most harmful to expose first. gate_error last.
var KIND_ORDER = ["nudity_or_children", "government_id", "credentials", "health_record",
  "bank_or_payment", "official_document", "private_message", "contact_details",
  "marked_confidential", "gate_error"];

// Words for actions. Colour is never the only signal: each has a word.
var ACTION_WORDS = {
  keep_image: "Keep as image",
  keep_text: "Turn into text",
  to_be_deleted: "Move to To Be Deleted"
};

// Friendly versions of what run.py prints in the terminal.
var STATES = {
  ollama: { eyebrow: "pip@shift ~ % can't reach helper", title: "Shift needs its helper app open",
    body: "I use an app called Ollama to look at screenshots. It isn't running right now.",
    steps: ["Open the Ollama app (it's in your Applications folder).", "Wait until its icon appears at the top of your screen.", "Come back here and press Try again."],
    primary: "Try again", secondary: "Do this later" },
  model: { eyebrow: "pip@shift ~ % one-time setup", title: "One more download, just once",
    body: "I need my reading model. It's a large download (several GB), so use Wi-Fi. You only do this once.",
    steps: ["Keep this window open.", "It can take 10 to 30 minutes.", "Nothing leaves your computer: this only downloads."],
    primary: "Start download", secondary: "Do this later" },
  empty: { eyebrow: "pip@shift ~ % nothing new", title: "All caught up",
    body: "No new screenshots since last time. I'll look again Sunday night.",
    steps: [], primary: "Close", secondary: "" },
  cap: { eyebrow: "pip@shift ~ % paused", title: "I looked at 10. The rest can wait.",
    body: "I look at up to 10 screenshots at a time so this never takes too long. The other 6 wait for next time.",
    steps: [], primary: "Review these 10", secondary: "Do this later" }
};
