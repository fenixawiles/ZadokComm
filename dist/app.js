const cases = {
  existing: {
    type: "Existing client · 5 years",
    initials: "AM",
    name: "Alex Morgan",
    meta: "Today at 11:42 AM · To Sarah",
    email: "Hey Sarah — any luck with the GMT we talked about? If you’ve got one, I can come by this afternoon.",
    context: [
      "Sarah is Alex’s advisor",
      "They discussed the GMT-Master II",
      "Alex purchased a Rolex in 2023",
    ],
    advisor: "Sarah",
    checks: [
      "Made the reply personal to Alex",
      "Did not reveal or promise inventory",
      "Used Sarah’s available appointment times",
    ],
    appointmentTitle: "Offer a time with Sarah",
    appointmentDescription: "Sarah is Alex’s advisor and has openings this afternoon.",
    times: ["2:30 PM", "4:00 PM"],
    draft: "Hi Alex,\n\nGreat to hear from you. I remember our conversation about the GMT-Master II. I’d be glad to connect this afternoon and continue the conversation in person.\n\nI have time at 2:30 or 4:00 today—would either work for you?\n\nSarah",
    alternate: "Hi Alex,\n\nGood to hear from you. I remember the GMT-Master II is still at the top of your list. Let’s reconnect in person this afternoon so I can take good care of you.\n\nI’m open at 2:30 or 4:00. Does one of those times suit you?\n\nSarah",
    withTime(time) {
      return `Hi Alex,\n\nGreat to hear from you. I remember our conversation about the GMT-Master II. I’d be glad to connect this afternoon and continue the conversation in person.\n\nI can reserve ${time} today for us—would that work for you?\n\nSarah`;
    },
  },
  new: {
    type: "First-time customer · No CRM match",
    initials: "JL",
    name: "Jordan Lee",
    meta: "Today at 12:18 PM · Website inquiry",
    email: "I’m looking for a steel Daytona. Do you have one available? I haven’t shopped with you before but I’m ready to purchase.",
    context: [
      "This email is not in the client database",
      "Jordan is interested in a Daytona",
      "The message shows strong purchase interest",
    ],
    advisor: "new-client team",
    checks: [
      "Welcomed Jordan as a first-time customer",
      "Did not imply that a watch is available",
      "Routed the visit to the new-client team",
    ],
    appointmentTitle: "Offer a first visit",
    appointmentDescription: "The new-client team has openings tomorrow in Houston.",
    times: ["10:30 AM", "1:00 PM"],
    draft: "Hi Jordan,\n\nThank you for reaching out and for considering Zadok. I’d be happy to learn more about what you’re looking for in a Daytona and introduce you to our watch team.\n\nWe can welcome you at our Houston showroom tomorrow at 10:30 AM or 1:00 PM. Would either time work for your first visit?\n\nMaya",
    alternate: "Hi Jordan,\n\nIt’s a pleasure to meet you. I’d be glad to talk through your interest in the Daytona and introduce you to our watch team.\n\nWe have first-visit openings tomorrow at 10:30 AM and 1:00 PM. Which would you prefer?\n\nMaya",
    withTime(time) {
      return `Hi Jordan,\n\nThank you for reaching out and for considering Zadok. I’d be happy to learn more about what you’re looking for in a Daytona and introduce you to our watch team.\n\nI can arrange a first visit at our Houston showroom tomorrow at ${time}. Would that work for you?\n\nMaya`;
    },
  },
};

const elements = {
  caseButtons: [...document.querySelectorAll(".case-button")],
  clientType: document.querySelector("#client-type"),
  clientInitials: document.querySelector("#client-initials"),
  clientName: document.querySelector("#client-name"),
  emailMeta: document.querySelector("#email-meta"),
  customerEmail: document.querySelector("#customer-email"),
  contextList: document.querySelector("#context-list"),
  replyRecipient: document.querySelector("#reply-recipient"),
  replyText: document.querySelector("#reply-text"),
  checksList: document.querySelector("#checks-list"),
  appointmentTitle: document.querySelector("#appointment-title"),
  appointmentDescription: document.querySelector("#appointment-description"),
  timeOptions: document.querySelector("#time-options"),
  useTimeButton: document.querySelector("#use-time-button"),
  prepareButton: document.querySelector("#prepare-button"),
  replyCard: document.querySelector("#reply-card"),
  rewriteButton: document.querySelector("#rewrite-button"),
  approveButton: document.querySelector("#approve-button"),
  toast: document.querySelector("#toast"),
  toastTitle: document.querySelector("#toast-title"),
  toastMessage: document.querySelector("#toast-message"),
};

let activeCase = "existing";
let selectedTime = cases.existing.times[0];
let alternateVisible = false;
let toastTimer;

function fillList(list, values, withChecks = false) {
  list.replaceChildren();
  values.forEach((value) => {
    const item = document.createElement("li");
    if (withChecks) {
      const check = document.createElement("span");
      check.textContent = "✓";
      item.append(check);
    }
    item.append(document.createTextNode(value));
    list.append(item);
  });
}

function renderTimes(example) {
  elements.timeOptions.replaceChildren();
  example.times.forEach((time, index) => {
    const button = document.createElement("button");
    button.className = `time-button${index === 0 ? " active" : ""}`;
    button.type = "button";
    button.textContent = time;
    button.addEventListener("click", () => selectTime(time));
    elements.timeOptions.append(button);
  });
  selectedTime = example.times[0];
}

function selectTime(time) {
  const example = cases[activeCase];
  if (!example.times.includes(time)) throw new Error("That time is not part of this example.");
  selectedTime = time;
  elements.timeOptions.querySelectorAll("button").forEach((button) => {
    button.classList.toggle("active", button.textContent === time);
  });
  elements.useTimeButton.classList.remove("used");
  elements.useTimeButton.textContent = `Use ${time} in reply`;
}

function renderCase(key, animate = true) {
  const example = cases[key];
  if (!example) throw new Error("Unknown demonstration case.");
  activeCase = key;
  alternateVisible = false;
  elements.caseButtons.forEach((button) => {
    const selected = button.dataset.case === key;
    button.classList.toggle("active", selected);
    button.setAttribute("aria-selected", String(selected));
  });
  elements.clientType.textContent = example.type;
  elements.clientInitials.textContent = example.initials;
  elements.clientName.textContent = example.name;
  elements.emailMeta.textContent = example.meta;
  elements.customerEmail.textContent = example.email;
  fillList(elements.contextList, example.context);
  elements.replyRecipient.textContent = example.name;
  elements.replyText.value = example.draft;
  fillList(elements.checksList, example.checks, true);
  elements.appointmentTitle.textContent = example.appointmentTitle;
  elements.appointmentDescription.textContent = example.appointmentDescription;
  renderTimes(example);
  elements.useTimeButton.classList.remove("used");
  elements.useTimeButton.textContent = `Use ${selectedTime} in reply`;
  elements.approveButton.textContent = key === "existing" ? "Mark ready for Sarah" : "Mark ready for new-client team";
  if (animate) animateReply();
  return { case: key, client: example.name };
}

function animateReply() {
  elements.replyCard.classList.remove("refreshing");
  requestAnimationFrame(() => elements.replyCard.classList.add("refreshing"));
}

function showToast(title, message) {
  window.clearTimeout(toastTimer);
  elements.toastTitle.textContent = title;
  elements.toastMessage.textContent = message;
  elements.toast.hidden = false;
  toastTimer = window.setTimeout(() => { elements.toast.hidden = true; }, 3600);
}

function useAppointmentTime(time = selectedTime) {
  const example = cases[activeCase];
  selectTime(time);
  elements.replyText.value = example.withTime(time);
  elements.useTimeButton.classList.add("used");
  elements.useTimeButton.textContent = `✓ ${time} added`;
  animateReply();
  showToast("Appointment time added", "The advisor can still edit the reply before sending it.");
  return { case: activeCase, client: example.name, time, status: "added_to_demo_reply" };
}

function markReady() {
  const example = cases[activeCase];
  showToast("Reply ready for advisor", `Prepared for ${example.advisor}. Nothing was sent.`);
  return { case: activeCase, client: example.name, status: "ready_for_advisor", sent: false };
}

elements.caseButtons.forEach((button) => button.addEventListener("click", () => renderCase(button.dataset.case)));
elements.useTimeButton.addEventListener("click", () => useAppointmentTime());
elements.approveButton.addEventListener("click", markReady);
elements.rewriteButton.addEventListener("click", () => {
  const example = cases[activeCase];
  alternateVisible = !alternateVisible;
  elements.replyText.value = alternateVisible ? example.alternate : example.draft;
  animateReply();
  showToast("Another version prepared", "It uses the same client facts and communication boundaries.");
});
elements.prepareButton.addEventListener("click", async () => {
  const label = elements.prepareButton.querySelector("span");
  elements.prepareButton.disabled = true;
  label.textContent = "Reading the email and client history…";
  await new Promise((resolve) => window.setTimeout(resolve, 850));
  label.textContent = "Preparing a careful response…";
  await new Promise((resolve) => window.setTimeout(resolve, 650));
  elements.replyText.value = cases[activeCase].draft;
  animateReply();
  label.textContent = "Reply prepared";
  await new Promise((resolve) => window.setTimeout(resolve, 650));
  label.textContent = "Prepare a tailored reply";
  elements.prepareButton.disabled = false;
});

function registerWebMcpTools() {
  const context = document.modelContext;
  if (!context?.registerTool) return;
  const lifecycle = new AbortController();
  const tools = [
    {
      name: "show_demo_case",
      title: "Show client example",
      description: "Show either the existing-client or first-time-customer communication example.",
      inputSchema: { type: "object", properties: { client_type: { type: "string", enum: ["existing", "new"] } }, required: ["client_type"], additionalProperties: false },
      annotations: { readOnlyHint: false, untrustedContentHint: false },
      execute(input) {
        if (!input || !cases[input.client_type]) throw new Error("client_type must be existing or new.");
        return renderCase(input.client_type);
      },
    },
    {
      name: "add_demo_appointment_time_to_reply",
      title: "Add appointment time to reply",
      description: "Put one of the currently displayed mock appointment times into the suggested reply. This schedules nothing.",
      inputSchema: { type: "object", properties: { time: { type: "string" } }, required: ["time"], additionalProperties: false },
      annotations: { readOnlyHint: false, untrustedContentHint: false },
      execute(input) {
        if (!input || typeof input.time !== "string") throw new Error("A displayed appointment time is required.");
        return useAppointmentTime(input.time);
      },
    },
    {
      name: "mark_demo_reply_ready",
      title: "Mark demo reply ready",
      description: "Mark the current synthetic reply ready for advisor review. Nothing is sent.",
      inputSchema: { type: "object", properties: {}, additionalProperties: false },
      annotations: { readOnlyHint: false, untrustedContentHint: false },
      execute() { return markReady(); },
    },
  ];
  tools.forEach((tool) => {
    try {
      void Promise.resolve(context.registerTool(tool, { signal: lifecycle.signal })).catch(() => {});
    } catch {
      // Browsers without WebMCP support still get the complete visible demo.
    }
  });
  window.addEventListener("pagehide", () => lifecycle.abort(), { once: true });
}

renderCase("existing", false);
registerWebMcpTools();
