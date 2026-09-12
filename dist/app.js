const scenarios = {
  existing: {
    number: "01",
    title: "Existing client asks about availability",
    name: "Alex Morgan",
    time: "Today, 11:42 AM",
    to: "To: Sarah Kline",
    body: "Hey Sarah — any luck with the GMT we talked about? If you’ve got one, I can come by this afternoon.",
    relationship: "Existing client",
    relationshipFact: "5 years",
    advisor: "Sarah Kline",
    interest: "GMT-Master II",
    activity: "Store visit · 42 days ago",
    historyYear: "2023",
    history: "Previous Rolex purchase",
    workflowIdentity: "Salesforce",
    policyCount: "2 policies",
    intent: "Availability inquiry",
    purchase: "High",
    strategy: "Maintain interest + invite",
    draftFor: "Response for Sarah to review",
    draft: [
      "Hi Alex,",
      "Great to hear from you. I remember our conversation about the GMT-Master II. I’d be glad to connect this afternoon and continue the conversation in person.",
      "I have time at 2:30 or 4:00 today—would either work for you?",
      "Sarah",
    ],
    alternateDraft: [
      "Hi Alex,",
      "Good to hear from you. I remember the GMT-Master II is still at the top of your list. Let’s reconnect in person this afternoon so I can take good care of you.",
      "I’m available at 2:30 or 4:00. Does one of those times suit you?",
      "Sarah",
    ],
    safetyTitle: "Sensitive inventory protected",
    safetyCopy: "The draft keeps Alex engaged without confirming inventory, allocation, or delivery timing.",
    appointmentHeading: "Offer an appointment",
    appointmentAdvisor: "Sarah Kline",
    appointmentInitials: "SK",
    appointmentReason: "Alex’s assigned representative",
    location: "Houston · Post Oak",
    date: "Today · Sep 11",
    slots: ["2:30 PM", "4:00 PM", "5:15 PM"],
    bookingNoun: "appointment",
    traceIdentity: "Exact email match · C-001",
    traceContext: "3 CRM records · 4 messages",
    tracePolicies: "Restricted inventory · No guarantee",
    traceRouting: "Assigned advisor · Sarah Kline",
    generic: "Thank you for your interest in the GMT-Master II. Availability may vary. Please contact the store or visit us for more information.",
    comparisonDraft: "Great to hear from you. I remember our conversation about the GMT-Master II. I’d be glad to connect this afternoon and continue the conversation in person.",
    comparisonClient: "Recognizes a five-year relationship",
    comparisonNext: "Offers Sarah’s actual available times",
  },
  new: {
    number: "02",
    title: "New prospect asks about a sought-after model",
    name: "Jordan Lee",
    time: "Today, 12:18 PM",
    to: "To: Web inquiries",
    body: "I’m looking for a steel Daytona. Do you have one available? I haven’t shopped with you before but I’m ready to purchase.",
    relationship: "New prospect",
    relationshipFact: "Not yet established",
    advisor: "Not assigned",
    interest: "Cosmograph Daytona",
    activity: "First inquiry",
    historyYear: "NEW",
    history: "No CRM purchase history found",
    workflowIdentity: "New email",
    policyCount: "3 policies",
    intent: "Availability inquiry",
    purchase: "High",
    strategy: "Welcome + establish relationship",
    draftFor: "Response for new-client team to review",
    draft: [
      "Hi Jordan,",
      "Thank you for reaching out and for considering Zadok. I’d be happy to learn more about what you’re looking for in a Daytona and introduce you to our watch team.",
      "We can welcome you at our Houston showroom tomorrow at 10:30 AM or 1:00 PM. Would either time work for your first visit?",
      "Maya",
    ],
    alternateDraft: [
      "Hi Jordan,",
      "It’s a pleasure to meet you. I’d be glad to talk through your interest in the Daytona and help you begin a relationship with our watch team.",
      "I can arrange an introduction tomorrow at 10:30 AM or 1:00 PM at our Houston showroom. Which time would you prefer?",
      "Maya",
    ],
    safetyTitle: "New-client expectations protected",
    safetyCopy: "The response welcomes Jordan without implying availability, a waitlist position, or an allocation promise.",
    appointmentHeading: "Arrange a first visit",
    appointmentAdvisor: "Maya Chen",
    appointmentInitials: "MC",
    appointmentReason: "First-time client concierge",
    location: "Houston · Post Oak",
    date: "Tomorrow · Sep 12",
    slots: ["10:30 AM", "1:00 PM", "3:30 PM"],
    bookingNoun: "first visit",
    traceIdentity: "No CRM match · New prospect",
    traceContext: "Inquiry only · PII minimized",
    tracePolicies: "Restricted inventory · No allocation promise",
    traceRouting: "New-client rotation · Maya Chen",
    generic: "Thank you for your inquiry. The Daytona is a popular model and availability is limited. Please visit our store to speak with a representative.",
    comparisonDraft: "It’s a pleasure to meet you. I’d be glad to talk through your interest in the Daytona and introduce you to our watch team tomorrow.",
    comparisonClient: "Recognizes and routes a first-time client",
    comparisonNext: "Offers the new-client team’s open times",
  },
  frustrated: {
    number: "03",
    title: "Frustrated client needs a careful follow-up",
    name: "Daniel Ruiz",
    time: "Today, 1:06 PM",
    to: "To: Michael Trent",
    body: "I’ve checked in three times about the Submariner and still haven’t heard anything useful. Am I actually being considered or not?",
    relationship: "Existing client",
    relationshipFact: "3 years",
    advisor: "Michael Trent",
    interest: "Submariner Date",
    activity: "Email follow-up · 18 days ago",
    historyYear: "2024",
    history: "Fine jewelry purchase",
    workflowIdentity: "Salesforce",
    policyCount: "4 policies",
    intent: "Complaint + allocation inquiry",
    purchase: "High",
    strategy: "Acknowledge + human follow-up",
    draftFor: "Escalated response for Michael to review",
    draft: [
      "Hi Daniel,",
      "I understand why the lack of a clear update has been frustrating, and I’m sorry we haven’t communicated more thoughtfully. I’d like to speak with you directly and review your interest in the Submariner together.",
      "I can call you at 3:15 today, or welcome you in at 5:00. Which would you prefer?",
      "Michael",
    ],
    alternateDraft: [
      "Hi Daniel,",
      "You’re right to expect a more personal follow-up from us. I’m sorry our recent communication has fallen short. I’d value the chance to reconnect directly about your Submariner interest.",
      "I’m available at 3:15 by phone or 5:00 in the showroom today. Please let me know what works best.",
      "Michael",
    ],
    safetyTitle: "Human escalation recommended",
    safetyCopy: "The draft acknowledges frustration without inventing status or promising an allocation. Michael remains the decision-maker.",
    appointmentHeading: "Prioritize advisor follow-up",
    appointmentAdvisor: "Michael Trent",
    appointmentInitials: "MT",
    appointmentReason: "Daniel’s assigned representative",
    location: "Houston · Phone or showroom",
    date: "Today · Sep 11",
    slots: ["3:15 PM", "5:00 PM", "Tomorrow 11 AM"],
    bookingNoun: "follow-up",
    traceIdentity: "Exact email match · C-008",
    traceContext: "5 CRM records · 7 messages",
    tracePolicies: "Complaint escalation · No status claim",
    traceRouting: "Priority review · Michael Trent",
    generic: "We apologize for the inconvenience. Demand is high and we cannot guarantee availability. Thank you for your patience.",
    comparisonDraft: "I understand why the lack of a clear update has been frustrating. I’d like to speak with you directly and review your interest together.",
    comparisonClient: "Acknowledges the specific service failure",
    comparisonNext: "Escalates to Daniel’s assigned advisor",
  },
  appointment: {
    number: "04",
    title: "Existing client requests a showroom visit",
    name: "Mia Chen",
    time: "Today, 2:34 PM",
    to: "To: Elena Ruiz",
    body: "Could I stop by Saturday to look at Datejust options? Late morning would be ideal if Elena is available.",
    relationship: "Existing client",
    relationshipFact: "2 years",
    advisor: "Elena Ruiz",
    interest: "Datejust 36",
    activity: "Purchase · 8 months ago",
    historyYear: "2025",
    history: "Anniversary jewelry purchase",
    workflowIdentity: "Salesforce",
    policyCount: "1 policy",
    intent: "Appointment request",
    purchase: "Medium",
    strategy: "Match advisor availability",
    draftFor: "Response for Elena to review",
    draft: [
      "Hi Mia,",
      "I’d love to see you and help you explore Datejust options. Elena is available Saturday morning and has openings at 10:30 and 11:45.",
      "Would you like me to reserve one of those times for you?",
      "Elena",
    ],
    alternateDraft: [
      "Hi Mia,",
      "It would be wonderful to have you back in the showroom. Elena can meet with you Saturday to explore Datejust options together.",
      "She has late-morning appointments at 10:30 and 11:45. Which works better for you?",
      "Elena",
    ],
    safetyTitle: "Appointment details verified",
    safetyCopy: "Only the advisor’s mock calendar availability is confirmed; no product availability is implied.",
    appointmentHeading: "Match requested availability",
    appointmentAdvisor: "Elena Ruiz",
    appointmentInitials: "ER",
    appointmentReason: "Mia’s requested representative",
    location: "Austin · The Domain",
    date: "Saturday · Sep 13",
    slots: ["10:30 AM", "11:45 AM", "2:00 PM"],
    bookingNoun: "showroom visit",
    traceIdentity: "Exact email match · C-009",
    traceContext: "2 CRM records · 3 messages",
    tracePolicies: "Calendar facts only",
    traceRouting: "Requested advisor · Elena Ruiz",
    generic: "Thank you for contacting us. Please call the store to confirm appointment availability for Saturday.",
    comparisonDraft: "Elena is available Saturday morning and can help you explore Datejust options at 10:30 or 11:45.",
    comparisonClient: "Remembers Mia’s assigned advisor",
    comparisonNext: "Matches the exact requested time window",
  },
  advisor: {
    number: "05",
    title: "Returning client asks for a previous advisor",
    name: "Priya Shah",
    time: "Today, 3:21 PM",
    to: "To: Client services",
    body: "Is James still with you? He helped me a few years ago and I’d like to reconnect about a watch for my husband’s birthday.",
    relationship: "Returning client",
    relationshipFact: "Since 2019",
    advisor: "James Ellis",
    interest: "Men’s milestone watch",
    activity: "Inactive · 3 years",
    historyYear: "2022",
    history: "James assisted prior purchase",
    workflowIdentity: "Salesforce",
    policyCount: "1 policy",
    intent: "Relationship follow-up",
    purchase: "Medium",
    strategy: "Reconnect with prior advisor",
    draftFor: "Response for James to review",
    draft: [
      "Hi Priya,",
      "It’s wonderful to hear from you. Yes, James is here, and I know he’ll be glad to reconnect and help you find something meaningful for your husband’s birthday.",
      "He has time tomorrow at 11:00 AM or 2:15 PM. Would either work for a call or showroom visit?",
      "Client Services",
    ],
    alternateDraft: [
      "Hi Priya,",
      "Welcome back. James is still with us and would be delighted to help with your husband’s birthday gift.",
      "He can connect tomorrow at 11:00 AM or 2:15 PM, either by phone or in the showroom. Which would you prefer?",
      "Client Services",
    ],
    safetyTitle: "Relationship continuity preserved",
    safetyCopy: "The response uses verified advisor history and mock availability without exposing internal client notes.",
    appointmentHeading: "Reconnect with prior advisor",
    appointmentAdvisor: "James Ellis",
    appointmentInitials: "JE",
    appointmentReason: "Priya’s previous representative",
    location: "Houston · Phone or showroom",
    date: "Tomorrow · Sep 12",
    slots: ["11:00 AM", "2:15 PM", "4:30 PM"],
    bookingNoun: "reconnection",
    traceIdentity: "Exact email match · C-007",
    traceContext: "4 CRM records · 2 messages",
    tracePolicies: "Verified relationship facts",
    traceRouting: "Previous advisor · James Ellis",
    generic: "Thank you for reaching out. Please contact our store to ask whether your previous salesperson is available.",
    comparisonDraft: "James is still with us and would be delighted to reconnect and help with your husband’s birthday gift.",
    comparisonClient: "Recovers the prior advisor relationship",
    comparisonNext: "Offers James’s matching availability",
  },
};

const elements = {
  select: document.querySelector("#scenario-select"),
  number: document.querySelector("#scenario-number"),
  title: document.querySelector("#scenario-title"),
  clientName: document.querySelector("#client-name"),
  messageTime: document.querySelector("#message-time"),
  messageTo: document.querySelector("#message-to"),
  messageBody: document.querySelector("#message-body"),
  relationshipPill: document.querySelector("#relationship-pill"),
  factRelationship: document.querySelector("#fact-relationship"),
  factAdvisor: document.querySelector("#fact-advisor"),
  factInterest: document.querySelector("#fact-interest"),
  factActivity: document.querySelector("#fact-activity"),
  historyYear: document.querySelector(".history-year"),
  historyText: document.querySelector("#history-text"),
  workflowIdentity: document.querySelector("#workflow-identity"),
  workflowPolicyCount: document.querySelector("#workflow-policy-count"),
  analysisIntent: document.querySelector("#analysis-intent"),
  analysisPurchase: document.querySelector("#analysis-purchase"),
  analysisStrategy: document.querySelector("#analysis-strategy"),
  draftHeading: document.querySelector("#draft-heading"),
  draftBox: document.querySelector("#draft-box"),
  safetyTitle: document.querySelector("#safety-title"),
  safetyCopy: document.querySelector("#safety-copy"),
  appointmentHeading: document.querySelector("#appointment-heading"),
  appointmentAdvisor: document.querySelector("#appointment-advisor"),
  appointmentInitials: document.querySelector("#appointment-initials"),
  appointmentReason: document.querySelector("#appointment-reason"),
  appointmentLocation: document.querySelector("#appointment-location"),
  appointmentDate: document.querySelector("#appointment-date"),
  slotList: document.querySelector("#slot-list"),
  bookButton: document.querySelector("#book-button"),
  traceIdentity: document.querySelector("#trace-identity"),
  traceContext: document.querySelector("#trace-context"),
  tracePolicies: document.querySelector("#trace-policies"),
  traceRouting: document.querySelector("#trace-routing"),
  genericResponse: document.querySelector("#generic-response"),
  comparisonDraft: document.querySelector("#comparison-draft"),
  comparisonClient: document.querySelector("#comparison-client-detail"),
  comparisonNext: document.querySelector("#comparison-next-step"),
  responseCard: document.querySelector(".response-card"),
  runButton: document.querySelector("#run-demo"),
  compareButton: document.querySelector("#compare-button"),
  dialog: document.querySelector("#comparison-dialog"),
  dialogClose: document.querySelector("#dialog-close"),
  approveButton: document.querySelector("#approve-button"),
  regenerateButton: document.querySelector("#regenerate-button"),
};

let activeScenarioKey = "existing";
let selectedSlot = scenarios.existing.slots[0];
let alternateDraftVisible = false;
let toastTimer;

function setDraft(paragraphs) {
  elements.draftBox.replaceChildren();
  paragraphs.forEach((paragraph, index) => {
    if (index > 0) elements.draftBox.append(document.createElement("br"), document.createElement("br"));
    elements.draftBox.append(document.createTextNode(paragraph));
  });
}

function renderSlots(scenario) {
  elements.slotList.replaceChildren();
  scenario.slots.forEach((slot, index) => {
    const button = document.createElement("button");
    button.className = `slot${index === 0 ? " active" : ""}`;
    button.type = "button";
    button.textContent = slot;
    button.addEventListener("click", () => selectSlot(slot));
    elements.slotList.append(button);
  });
  selectedSlot = scenario.slots[0];
}

function updateBookingButton(scenario) {
  elements.bookButton.classList.remove("confirmed");
  elements.bookButton.textContent = `Prepare ${selectedSlot} ${scenario.bookingNoun}`;
}

function selectSlot(slot) {
  const scenario = scenarios[activeScenarioKey];
  selectedSlot = slot;
  elements.slotList.querySelectorAll(".slot").forEach((button) => {
    button.classList.toggle("active", button.textContent === slot);
  });
  updateBookingButton(scenario);
}

function renderScenario(key, { animate = false } = {}) {
  const scenario = scenarios[key];
  if (!scenario) return;
  activeScenarioKey = key;
  alternateDraftVisible = false;
  elements.select.value = key;
  elements.number.textContent = `DEMO SCENARIO ${scenario.number}`;
  elements.title.textContent = scenario.title;
  elements.clientName.textContent = scenario.name;
  elements.messageTime.textContent = scenario.time;
  elements.messageTo.textContent = scenario.to;
  elements.messageBody.textContent = scenario.body;
  elements.relationshipPill.textContent = scenario.relationship;
  elements.factRelationship.textContent = scenario.relationshipFact;
  elements.factAdvisor.textContent = scenario.advisor;
  elements.factInterest.textContent = scenario.interest;
  elements.factActivity.textContent = scenario.activity;
  elements.historyYear.textContent = scenario.historyYear;
  elements.historyText.textContent = scenario.history;
  elements.workflowIdentity.textContent = scenario.workflowIdentity;
  elements.workflowPolicyCount.textContent = scenario.policyCount;
  elements.analysisIntent.textContent = scenario.intent;
  elements.analysisPurchase.textContent = scenario.purchase;
  elements.analysisStrategy.textContent = scenario.strategy;
  elements.draftHeading.textContent = scenario.draftFor;
  setDraft(scenario.draft);
  elements.safetyTitle.textContent = scenario.safetyTitle;
  elements.safetyCopy.textContent = scenario.safetyCopy;
  elements.appointmentHeading.textContent = scenario.appointmentHeading;
  elements.appointmentAdvisor.textContent = scenario.appointmentAdvisor;
  elements.appointmentInitials.textContent = scenario.appointmentInitials;
  elements.appointmentReason.textContent = scenario.appointmentReason;
  elements.appointmentLocation.textContent = scenario.location;
  elements.appointmentDate.textContent = scenario.date;
  renderSlots(scenario);
  updateBookingButton(scenario);
  elements.traceIdentity.textContent = scenario.traceIdentity;
  elements.traceContext.textContent = scenario.traceContext;
  elements.tracePolicies.textContent = scenario.tracePolicies;
  elements.traceRouting.textContent = scenario.traceRouting;
  elements.genericResponse.textContent = scenario.generic;
  elements.comparisonDraft.textContent = scenario.comparisonDraft;
  elements.comparisonClient.textContent = scenario.comparisonClient;
  elements.comparisonNext.textContent = scenario.comparisonNext;
  if (animate) {
    elements.responseCard.classList.remove("refreshing");
    requestAnimationFrame(() => elements.responseCard.classList.add("refreshing"));
  }
}

function showToast(title, message) {
  window.clearTimeout(toastTimer);
  document.querySelector(".toast")?.remove();
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.setAttribute("role", "status");
  const check = document.createElement("span");
  check.className = "toast-check";
  check.textContent = "✓";
  const copy = document.createElement("div");
  const strong = document.createElement("strong");
  strong.textContent = title;
  const detail = document.createElement("span");
  detail.textContent = message;
  copy.append(strong, detail);
  toast.append(check, copy);
  document.body.append(toast);
  toastTimer = window.setTimeout(() => toast.remove(), 4200);
}

function prepareBooking(slot = selectedSlot) {
  const scenario = scenarios[activeScenarioKey];
  if (!scenario.slots.includes(slot)) throw new Error("That time is not available in this demo scenario.");
  selectSlot(slot);
  elements.bookButton.classList.add("confirmed");
  elements.bookButton.textContent = `✓ ${slot} ${scenario.bookingNoun} prepared`;
  showToast("Demo appointment prepared", `${scenario.name} · ${scenario.appointmentAdvisor} · ${slot}. No calendar event was created.`);
  return { scenario: activeScenarioKey, client: scenario.name, advisor: scenario.appointmentAdvisor, slot, status: "demo_prepared" };
}

function approveDraft() {
  const scenario = scenarios[activeScenarioKey];
  showToast("Draft moved to review queue", `${scenario.name}’s draft was saved for the advisor. Nothing was sent.`);
  return { scenario: activeScenarioKey, client: scenario.name, status: "approved_for_demo_review", sent: false };
}

function openDialog() {
  elements.dialog.hidden = false;
  document.body.style.overflow = "hidden";
  elements.dialogClose.focus();
}

function closeDialog() {
  elements.dialog.hidden = true;
  document.body.style.overflow = "";
  elements.compareButton.focus();
}

async function runScenario() {
  const label = elements.runButton.querySelector("span");
  const steps = [...document.querySelectorAll(".workflow-step")];
  elements.runButton.disabled = true;
  steps.forEach((step) => step.classList.remove("complete", "current"));
  const labels = ["Resolving client…", "Gathering context…", "Applying guardrails…", "Drafting response…"];
  for (let index = 0; index < steps.length; index += 1) {
    label.textContent = labels[index];
    if (index > 0) steps[index - 1].classList.replace("current", "complete");
    steps[index].classList.add("current");
    await new Promise((resolve) => window.setTimeout(resolve, 330));
  }
  steps[3].classList.add("complete");
  renderScenario(activeScenarioKey, { animate: true });
  label.textContent = "Draft ready";
  await new Promise((resolve) => window.setTimeout(resolve, 650));
  label.textContent = "Run this scenario";
  elements.runButton.disabled = false;
}

elements.select.addEventListener("change", (event) => renderScenario(event.target.value, { animate: true }));
elements.runButton.addEventListener("click", runScenario);
elements.compareButton.addEventListener("click", openDialog);
elements.dialogClose.addEventListener("click", closeDialog);
elements.dialog.addEventListener("click", (event) => {
  if (event.target === elements.dialog) closeDialog();
});
elements.bookButton.addEventListener("click", () => prepareBooking());
elements.approveButton.addEventListener("click", approveDraft);
elements.regenerateButton.addEventListener("click", () => {
  const scenario = scenarios[activeScenarioKey];
  alternateDraftVisible = !alternateDraftVisible;
  setDraft(alternateDraftVisible ? scenario.alternateDraft : scenario.draft);
  elements.responseCard.classList.remove("refreshing");
  requestAnimationFrame(() => elements.responseCard.classList.add("refreshing"));
  showToast("Alternative draft generated", "The same client context and policy guardrails were preserved.");
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !elements.dialog.hidden) closeDialog();
});

function registerWebMcpTools() {
  const context = document.modelContext;
  if (!context?.registerTool) return;
  const lifecycle = new AbortController();
  const registrations = [
    {
      name: "select_demo_scenario",
      title: "Select demo scenario",
      description: "Select and display one of the synthetic client communication scenarios.",
      inputSchema: {
        type: "object",
        properties: { scenario: { type: "string", enum: Object.keys(scenarios) } },
        required: ["scenario"],
        additionalProperties: false,
      },
      annotations: { readOnlyHint: false, untrustedContentHint: false },
      execute(input) {
        if (!input || !scenarios[input.scenario]) throw new Error("Choose a valid synthetic scenario.");
        renderScenario(input.scenario, { animate: true });
        return { scenario: input.scenario, client: scenarios[input.scenario].name };
      },
    },
    {
      name: "prepare_demo_appointment",
      title: "Prepare demo appointment",
      description: "Prepare a mock appointment using one of the visible available times. No real calendar event is created.",
      inputSchema: {
        type: "object",
        properties: { slot: { type: "string" } },
        required: ["slot"],
        additionalProperties: false,
      },
      annotations: { readOnlyHint: false, untrustedContentHint: false },
      execute(input) {
        if (!input || typeof input.slot !== "string") throw new Error("A visible appointment time is required.");
        return prepareBooking(input.slot);
      },
    },
    {
      name: "approve_demo_draft",
      title: "Approve demo draft",
      description: "Save the visible draft to the synthetic human-review queue without sending it to a client.",
      inputSchema: { type: "object", properties: {}, additionalProperties: false },
      annotations: { readOnlyHint: false, untrustedContentHint: false },
      execute() {
        return approveDraft();
      },
    },
  ];
  registrations.forEach((tool) => {
    try {
      void Promise.resolve(context.registerTool(tool, { signal: lifecycle.signal })).catch(() => {});
    } catch {
      // WebMCP is optional in browsers that do not yet support registration.
    }
  });
  window.addEventListener("pagehide", () => lifecycle.abort(), { once: true });
}

renderScenario("existing");
registerWebMcpTools();
