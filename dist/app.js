const conversations = {
  alex: {
    name: "Alex Morgan",
    initials: "AM",
    avatarClass: "avatar-green",
    subtitle: "Existing client · Email",
    advisor: "Sarah",
    context: [
      ["Advisor", "Sarah Kline"],
      ["Relationship", "5 years"],
      ["Interest", "GMT-Master II"],
      ["History", "Rolex purchase · 2023"],
    ],
    messages: [
      { direction: "outgoing", author: "Sarah", time: "Aug 19 · 3:14 PM", text: "It was great seeing you, Alex. I’ve made a note that the GMT-Master II remains your first choice, and I’ll keep our conversation in mind." },
      { direction: "incoming", author: "Alex", time: "Today · 11:42 AM", text: "Hey Sarah — any luck with the GMT we talked about? If you’ve got one, I can come by this afternoon." },
    ],
    drafts: [
      "Hi Alex,\n\nGood to hear from you. I remember our conversation about the GMT-Master II. I don’t have an availability update I can confirm for you today, but your interest remains noted and I’ll reach out personally when I have a meaningful update.\n\nSarah",
      "Hi Alex,\n\nThanks for checking in. I remember the GMT-Master II is your first choice. I don’t have a new availability update to share today, but I’ll stay in touch directly when there is something meaningful to discuss.\n\nSarah",
    ],
    schedule: null,
  },
  mia: {
    name: "Mia Chen",
    initials: "MC",
    avatarClass: "avatar-gold",
    subtitle: "Existing client · Email",
    advisor: "Elena",
    context: [
      ["Advisor", "Elena Ruiz"],
      ["Relationship", "2 years"],
      ["Interest", "Datejust 36"],
      ["History", "Anniversary jewelry · 2025"],
    ],
    messages: [
      { direction: "outgoing", author: "Elena", time: "Jun 6 · 10:22 AM", text: "I hope you’re still enjoying the anniversary piece. It was a pleasure helping you select it." },
      { direction: "incoming", author: "Mia", time: "Today · 10:18 AM", text: "Could I stop by Saturday to look at Datejust options? Late morning would be ideal if Elena is available." },
    ],
    drafts: [
      "Hi Mia,\n\nYes, I’d be happy to see you Saturday and help you explore Datejust options. I’m available at 10:30 AM or 11:45 AM. Would either time work for you?\n\nElena",
      "Hi Mia,\n\nI’d love to have you back in the showroom. I can meet with you Saturday to look at Datejust options, with openings at 10:30 AM and 11:45 AM. Which works better for you?\n\nElena",
    ],
    schedule: "Elena is available Saturday at 10:30 AM and 11:45 AM.",
  },
  daniel: {
    name: "Daniel Ruiz",
    initials: "DR",
    avatarClass: "avatar-slate",
    subtitle: "Existing client · Email",
    advisor: "Michael",
    context: [
      ["Advisor", "Michael Trent"],
      ["Relationship", "3 years"],
      ["Interest", "Submariner Date"],
      ["Last contact", "18 days ago"],
    ],
    messages: [
      { direction: "outgoing", author: "Michael", time: "Aug 22 · 4:08 PM", text: "I appreciate you checking in, Daniel. I’ll reach out directly if I have a meaningful update for you." },
      { direction: "incoming", author: "Daniel", time: "Yesterday · 4:36 PM", text: "I’ve checked in three times about the Submariner and still haven’t heard anything useful. Am I actually being considered or not?" },
    ],
    drafts: [
      "Hi Daniel,\n\nYou’re right to expect clearer communication from me, and I’m sorry my recent follow-up has fallen short. I don’t have a new allocation update to give you today. Your interest in the Submariner remains noted, and I will contact you personally when I have meaningful information to share.\n\nMichael",
      "Hi Daniel,\n\nI understand your frustration, and I’m sorry I haven’t communicated more thoughtfully. I don’t have a new Submariner update for you today, but your interest remains active and I will handle future follow-up with you directly.\n\nMichael",
    ],
    schedule: null,
  },
  jordan: {
    name: "Jordan Lee",
    initials: "JL",
    avatarClass: "avatar-blue",
    subtitle: "New customer · Website inquiry",
    advisor: "New-client team",
    context: [
      ["CRM match", "No existing record"],
      ["Relationship", "First inquiry"],
      ["Interest", "Steel Daytona"],
      ["Purchase intent", "High"],
    ],
    messages: [
      { direction: "incoming", author: "Jordan", time: "Tuesday · 2:07 PM", text: "I’m looking for a steel Daytona. Do you have one available? I haven’t shopped with you before but I’m ready to purchase." },
    ],
    drafts: [
      "Hi Jordan,\n\nThank you for reaching out and for considering Zadok. The steel Daytona receives significant interest, and I’m not able to confirm availability by email. I’d be glad to learn more about what you’re looking for and help you begin a conversation with our watch team.\n\nMaya",
      "Hi Jordan,\n\nIt’s a pleasure to meet you, and thank you for contacting Zadok. I can’t confirm availability of a steel Daytona through email, but I’d be happy to learn more about your preferences and introduce you to our watch team.\n\nMaya",
    ],
    schedule: null,
  },
};

const elements = {
  conversationButtons: [...document.querySelectorAll(".conversation")],
  headerAvatar: document.querySelector("#header-avatar"),
  headerName: document.querySelector("#header-name"),
  headerSubtitle: document.querySelector("#header-subtitle"),
  contextPanel: document.querySelector("#context-panel"),
  contextCount: document.querySelector("#context-count"),
  contextContent: document.querySelector("#context-content"),
  messages: document.querySelector("#messages"),
  draftTitle: document.querySelector("#draft-title"),
  draftStatus: document.querySelector("#draft-status"),
  scheduleNote: document.querySelector("#schedule-note"),
  scheduleCopy: document.querySelector("#schedule-copy"),
  draftText: document.querySelector("#draft-text"),
  regenerateButton: document.querySelector("#regenerate-button"),
  editButton: document.querySelector("#edit-button"),
  sendButton: document.querySelector("#send-button"),
  composer: document.querySelector(".composer"),
};

let activeId = "alex";
let draftIndex = 0;
let editing = false;
const sentReplies = new Set();

function renderContext(conversation) {
  const list = document.createElement("dl");
  conversation.context.forEach(([label, value]) => {
    const row = document.createElement("div");
    const term = document.createElement("dt");
    const description = document.createElement("dd");
    term.textContent = label;
    description.textContent = value;
    row.append(term, description);
    list.append(row);
  });
  const note = document.createElement("p");
  note.textContent = "Mock CRM context. Used silently to prepare the draft.";
  elements.contextContent.replaceChildren(list, note);
  elements.contextCount.textContent = `${conversation.context.length} details`;
}

function appendMessage(message) {
  const article = document.createElement("article");
  article.className = `message ${message.direction}`;
  const label = document.createElement("div");
  label.className = "message-label";
  const author = document.createElement("strong");
  author.textContent = message.author;
  const time = document.createElement("time");
  time.textContent = message.time;
  const body = document.createElement("p");
  body.textContent = message.text;
  label.append(author, time);
  article.append(label, body);
  elements.messages.append(article);
}

function renderMessages(conversation) {
  const divider = document.createElement("div");
  divider.className = "date-divider";
  const label = document.createElement("span");
  label.textContent = "Conversation";
  divider.append(label);
  elements.messages.replaceChildren(divider);
  conversation.messages.forEach(appendMessage);
  if (sentReplies.has(activeId)) {
    appendMessage({
      direction: "outgoing",
      author: conversation.advisor,
      time: "Now · Demo",
      text: elements.draftText.dataset.sentText || conversation.drafts[draftIndex],
    });
  }
  elements.messages.scrollTop = elements.messages.scrollHeight;
}

function animateComposer() {
  elements.composer.classList.remove("refreshing");
  requestAnimationFrame(() => elements.composer.classList.add("refreshing"));
}

function setEditing(next) {
  editing = next;
  elements.draftText.readOnly = !next;
  elements.editButton.classList.toggle("active", next);
  elements.editButton.textContent = next ? "Editing" : "Edit";
  if (next) {
    elements.draftText.focus();
    elements.draftText.setSelectionRange(elements.draftText.value.length, elements.draftText.value.length);
  }
  return { conversation: activeId, editing };
}

function renderConversation(id, animate = true) {
  const conversation = conversations[id];
  if (!conversation) throw new Error("Unknown conversation.");
  activeId = id;
  draftIndex = 0;
  elements.contextPanel.open = false;
  elements.conversationButtons.forEach((button) => {
    const active = button.dataset.conversation === id;
    button.classList.toggle("active", active);
    button.setAttribute("aria-current", active ? "true" : "false");
    if (active) button.querySelector(".conversation-meta i")?.classList.add("seen");
  });
  elements.headerAvatar.className = `avatar ${conversation.avatarClass}`;
  elements.headerAvatar.textContent = conversation.initials;
  elements.headerName.textContent = conversation.name;
  elements.headerSubtitle.textContent = conversation.subtitle;
  renderContext(conversation);
  elements.draftTitle.textContent = `Reply to ${conversation.name.split(" ")[0]}`;
  elements.draftStatus.textContent = "Drafted automatically when the message arrived";
  elements.draftText.value = conversation.drafts[0];
  elements.draftText.dataset.sentText = "";
  elements.scheduleNote.hidden = !conversation.schedule;
  elements.scheduleCopy.textContent = conversation.schedule || "";
  sentReplies.delete(id);
  renderMessages(conversation);
  setEditing(false);
  elements.regenerateButton.disabled = false;
  elements.editButton.disabled = false;
  elements.sendButton.disabled = false;
  elements.sendButton.textContent = "Send";
  if (animate) animateComposer();
  return { conversation: id, client: conversation.name, scheduling_used: Boolean(conversation.schedule) };
}

async function regenerateDraft() {
  const conversation = conversations[activeId];
  elements.regenerateButton.disabled = true;
  elements.regenerateButton.textContent = "Regenerating…";
  elements.draftStatus.textContent = "Writing another response to the current question";
  await new Promise((resolve) => window.setTimeout(resolve, 650));
  draftIndex = (draftIndex + 1) % conversation.drafts.length;
  elements.draftText.value = conversation.drafts[draftIndex];
  elements.draftStatus.textContent = "Alternative drafted from the same conversation";
  elements.regenerateButton.textContent = "Regenerate";
  elements.regenerateButton.disabled = false;
  animateComposer();
  return { conversation: activeId, draft_version: draftIndex + 1 };
}

function replaceDraft(text) {
  if (typeof text !== "string" || !text.trim()) throw new Error("Reply text cannot be empty.");
  elements.draftText.value = text;
  elements.draftStatus.textContent = "Edited by the advisor";
  return { conversation: activeId, length: text.length };
}

function sendDemoReply() {
  const text = elements.draftText.value.trim();
  if (!text) throw new Error("Reply text cannot be empty.");
  const conversation = conversations[activeId];
  elements.draftText.dataset.sentText = text;
  sentReplies.add(activeId);
  renderMessages(conversation);
  elements.draftText.value = "";
  elements.draftText.placeholder = "Reply shown in the conversation above.";
  elements.draftStatus.textContent = "Added to this mock conversation · Nothing was transmitted";
  setEditing(false);
  elements.regenerateButton.disabled = true;
  elements.editButton.disabled = true;
  elements.sendButton.disabled = true;
  elements.sendButton.textContent = "Sent";
  return { conversation: activeId, status: "added_to_mock_thread", transmitted: false };
}

elements.conversationButtons.forEach((button) => {
  button.addEventListener("click", () => renderConversation(button.dataset.conversation));
});
elements.regenerateButton.addEventListener("click", regenerateDraft);
elements.editButton.addEventListener("click", () => setEditing(!editing));
elements.sendButton.addEventListener("click", sendDemoReply);

function registerWebMcpTools() {
  const context = document.modelContext;
  if (!context?.registerTool) return;
  const lifecycle = new AbortController();
  const tools = [
    {
      name: "open_mock_crm_conversation",
      title: "Open CRM conversation",
      description: "Open one synthetic client conversation and its automatically prepared reply.",
      inputSchema: {
        type: "object",
        properties: { conversation: { type: "string", enum: Object.keys(conversations) } },
        required: ["conversation"],
        additionalProperties: false,
      },
      annotations: { readOnlyHint: false, untrustedContentHint: false },
      execute(input) {
        if (!input || !conversations[input.conversation]) throw new Error("Choose a valid conversation.");
        return renderConversation(input.conversation);
      },
    },
    {
      name: "regenerate_mock_reply",
      title: "Regenerate reply",
      description: "Replace the proposed reply with another draft that addresses the same current message.",
      inputSchema: { type: "object", properties: {}, additionalProperties: false },
      annotations: { readOnlyHint: false, untrustedContentHint: false },
      execute() { return regenerateDraft(); },
    },
    {
      name: "edit_mock_reply",
      title: "Edit reply",
      description: "Replace the proposed reply text in the mock CRM composer.",
      inputSchema: {
        type: "object",
        properties: { text: { type: "string", minLength: 1 } },
        required: ["text"],
        additionalProperties: false,
      },
      annotations: { readOnlyHint: false, untrustedContentHint: false },
      execute(input) { return replaceDraft(input?.text); },
    },
    {
      name: "send_mock_reply",
      title: "Send reply in demo",
      description: "Add the current reply to the synthetic conversation. This transmits nothing outside the mockup.",
      inputSchema: { type: "object", properties: {}, additionalProperties: false },
      annotations: { readOnlyHint: false, untrustedContentHint: false },
      execute() { return sendDemoReply(); },
    },
  ];
  tools.forEach((tool) => {
    try {
      void Promise.resolve(context.registerTool(tool, { signal: lifecycle.signal })).catch(() => {});
    } catch {
      // The visible demo remains fully usable when WebMCP is unavailable.
    }
  });
  window.addEventListener("pagehide", () => lifecycle.abort(), { once: true });
}

renderConversation("alex", false);
registerWebMcpTools();
