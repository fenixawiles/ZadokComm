/* Inbox front end: hydrates the three-pane shell from the JSON APIs.
   Interaction model carried over from the concept demo (draft-on-arrival,
   Send / Edit / Regenerate), extended with triage badges, SLA aging, flag
   acknowledgment, profile-change cards, and the assist-scope toggle. */

const $ = (id) => document.getElementById(id);
const app = $("app");

const AVATAR_CLASSES = ["avatar-green", "avatar-gold", "avatar-slate", "avatar-blue"];
const state = { threads: [], activeId: null, thread: null, editing: false, ackArmed: false };

function initials(name) {
  return name.split(/\s+/).map((w) => w[0] || "").join("").slice(0, 2).toUpperCase();
}

function avatarClass(id) {
  return AVATAR_CLASSES[id % AVATAR_CLASSES.length];
}

function fmtAgo(iso) {
  if (!iso) return "";
  const hours = Math.max(0, (Date.now() - new Date(iso).getTime()) / 36e5);
  if (hours < 1) return `${Math.max(1, Math.round(hours * 60))}m`;
  if (hours < 48) return `${Math.round(hours)}h`;
  return `${Math.round(hours / 24)}d`;
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const body = await res.json().catch(() => ({}));
  return { ok: res.ok, status: res.status, body };
}

/* ------------------------------------------------------------ thread list */

async function loadThreads() {
  const { body } = await api("/api/threads");
  state.threads = body.threads || [];
  renderScope(body.assist_scope);
  renderThreadList();
  if (state.activeId === null && state.threads.length) openThread(state.threads[0].id);
}

const BADGES = {
  ready: ["badge-ready", "Ready to review"],
  needs_attention: ["badge-attention", "Needs attention"],
  personal: ["badge-personal", "Answer personally"],
  failed: ["badge-failed", "Draft failed"],
};

function renderThreadList() {
  const list = $("conversation-list");
  list.replaceChildren(
    ...state.threads.map((thread) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "conversation" + (thread.id === state.activeId ? " active" : "");
      button.addEventListener("click", () => openThread(thread.id));

      const avatar = document.createElement("span");
      avatar.className = `avatar ${avatarClass(thread.id)}`;
      avatar.textContent = initials(thread.client_display_name);

      const copy = document.createElement("span");
      copy.className = "conversation-copy";
      const name = document.createElement("strong");
      name.textContent = thread.client_display_name;
      const snippet = document.createElement("small");
      snippet.textContent = thread.snippet;
      copy.append(name, snippet);

      const meta = document.createElement("span");
      meta.className = "conversation-meta";
      const wait = document.createElement("span");
      if (thread.waiting.since) {
        wait.className = "wait-chip" + (thread.waiting.overdue ? " overdue" : "");
        wait.textContent = thread.waiting.overdue
          ? `${fmtAgo(thread.waiting.since)} · overdue`
          : `${fmtAgo(thread.waiting.since)} waiting`;
      } else {
        wait.className = "wait-chip";
        wait.textContent = fmtAgo(thread.last_inbound_at);
      }
      meta.append(wait);
      if (thread.badge && BADGES[thread.badge]) {
        const [cls, label] = BADGES[thread.badge];
        const badge = document.createElement("span");
        badge.className = `badge ${cls}`;
        badge.textContent = label;
        meta.append(badge);
      }
      button.append(avatar, copy, meta);
      return button;
    })
  );
}

/* ------------------------------------------------------------ assist scope */

function renderScope(scope) {
  if (!scope) return;
  $("scope-label").textContent = scope === "all" ? "All inquiries" : "Simple inquiries only";
  $("scope-toggle").textContent = scope === "all" ? "Return to simple only" : "Expand to all inquiries";
  $("scope-toggle").dataset.next = scope === "all" ? "routine_only" : "all";
}

$("scope-toggle").addEventListener("click", async () => {
  const next = $("scope-toggle").dataset.next;
  const prompt =
    next === "all"
      ? "Expand assist scope? New complex inquiries will also arrive with a draft (marked for careful review). Every send still requires advisor approval."
      : "Return to simple inquiries only? Complex messages will again wait for a personal reply.";
  if (!window.confirm(prompt)) return;
  const { body } = await api("/api/settings/assist-scope", {
    method: "POST",
    body: JSON.stringify({ assist_scope: next }),
  });
  renderScope(body.assist_scope);
});

/* ------------------------------------------------------------- thread view */

async function openThread(threadId) {
  state.activeId = threadId;
  state.editing = false;
  state.ackArmed = false;
  renderThreadList();
  const { ok, body } = await api(`/api/threads/${threadId}`);
  // A slower response for a thread the advisor has already left must not
  // render over the current selection (its action buttons would then target
  // the wrong draft).
  if (!ok || state.activeId !== threadId) return;
  state.thread = body;
  renderThread(true);
}

async function refreshThread() {
  const threadId = state.activeId;
  const { ok, body } = await api(`/api/threads/${threadId}`);
  if (ok && state.activeId === threadId) {
    state.thread = body;
    renderThread(false);
  }
  loadThreads();
}

function renderContext(context) {
  const list = document.createElement("dl");
  context.forEach(([label, value]) => {
    const row = document.createElement("div");
    const term = document.createElement("dt");
    term.textContent = label;
    const description = document.createElement("dd");
    description.textContent = value;
    row.append(term, description);
    list.append(row);
  });
  const note = document.createElement("p");
  note.textContent = "Mock CRM context. Used silently to prepare the draft.";
  $("context-content").replaceChildren(list, note);
  $("context-count").textContent = `${context.length} details`;
}

function renderMessages(messages) {
  const container = $("messages");
  const divider = document.createElement("div");
  divider.className = "date-divider";
  const label = document.createElement("span");
  label.textContent = "Conversation";
  divider.append(label);
  container.replaceChildren(divider);
  messages.forEach((message) => {
    const article = document.createElement("article");
    article.className = `message ${message.direction === "outbound" ? "outgoing" : "incoming"}`;
    const head = document.createElement("div");
    head.className = "message-label";
    const author = document.createElement("strong");
    author.textContent = message.sender;
    const time = document.createElement("time");
    time.textContent = `${fmtAgo(message.occurred_at)} ago`;
    head.append(author, time);
    const body = document.createElement("p");
    body.textContent = message.body;
    article.append(head, body);
    container.append(article);
  });
  container.scrollTop = container.scrollHeight;
}

function renderProfileCards(target, cards) {
  target.replaceChildren(
    ...cards.map((card) => {
      const wrap = document.createElement("div");
      wrap.className = "profile-card";
      const copy = document.createElement("div");
      const title = document.createElement("strong");
      title.textContent = `Client asked to update: ${card.requested_change}`;
      const quote = document.createElement("q");
      quote.textContent = card.quote;
      copy.append(title, quote);
      const actions = document.createElement("div");
      actions.className = "profile-card-actions";
      [["acknowledge", "Acknowledge"], ["dismiss", "Dismiss"]].forEach(([action, text]) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "button button-secondary";
        button.textContent = text;
        button.addEventListener("click", async () => {
          await api(`/api/profile-changes/${card.id}/${action}`, { method: "POST" });
          refreshThread();
        });
        actions.append(button);
      });
      wrap.append(copy, actions);
      return wrap;
    })
  );
}

function statusLine(draft) {
  if (draft.status === "edited") return "Edited by the advisor";
  if (draft.status === "needs_attention") return "Drafted automatically — review the flagged wording";
  if (draft.outcome !== "completed") return `Drafting failed (${draft.outcome}) — regenerate to retry`;
  if (draft.version > 1) return "Alternative drafted from the same conversation";
  return "Drafted automatically when the message arrived";
}

function renderFlags(draft) {
  const banner = $("flag-banner");
  const flags = draft ? draft.flags : [];
  if (!flags || !flags.length) {
    banner.hidden = true;
    $("composer").classList.remove("attention");
    return;
  }
  banner.hidden = false;
  $("composer").classList.add("attention");
  $("flag-banner-title").textContent = "Needs attention — protocol scan";
  $("flag-list").replaceChildren(
    ...flags.map((flag) => {
      const item = document.createElement("li");
      item.textContent = `${flag.label}`;
      if (flag.matched_span) {
        const em = document.createElement("em");
        em.textContent = ` “${flag.matched_span}”`;
        item.append(em);
      }
      return item;
    })
  );
  $("flag-ack-row").hidden = !state.ackArmed;
}

function renderThread(animate) {
  const data = state.thread;
  if (!data) return;
  $("empty-pane").hidden = true;
  $("thread-pane").hidden = false;

  $("header-avatar").className = `avatar ${avatarClass(data.thread.id)}`;
  $("header-avatar").textContent = initials(data.thread.client_display_name);
  $("header-name").textContent = data.thread.client_display_name;
  $("header-subtitle").textContent = data.thread.subtitle;
  $("history-panel").open = false;
  $("context-panel").open = false;
  $("history-count").textContent = "";

  renderContext(data.context);
  renderMessages(data.messages);

  const composer = $("composer");
  const personalBlock = $("personal-block");
  const quietBlock = $("quiet-block");
  composer.hidden = true;
  personalBlock.hidden = true;
  quietBlock.hidden = true;

  const draft = data.draft;
  const lastInbound = [...data.messages].reverse().find((m) => m.direction === "inbound");

  if (draft) {
    composer.hidden = false;
    const failed = draft.status === "failed";
    $("draft-title").textContent = `Reply to ${data.thread.client_display_name.split(" ")[0]}`;
    $("draft-status").textContent = statusLine(draft);
    $("complex-chip").hidden = !(lastInbound && lastInbound.triage === "personal" && !failed);
    $("draft-text").value = failed ? "" : draft.text;
    $("draft-text").readOnly = !state.editing;
    $("schedule-note").hidden = !data.schedule_note;
    $("schedule-copy").textContent = data.schedule_note || "";
    renderProfileCards($("profile-cards"), data.profile_changes);
    renderFlags(failed ? null : draft);
    $("send-button").disabled = failed;
    $("edit-button").disabled = failed;
    $("edit-button").textContent = state.editing ? "Done" : "Edit";
    $("edit-button").classList.toggle("active", state.editing);
    $("regenerate-button").disabled = false;
    $("discard-button").disabled = failed;
    if (animate) {
      composer.classList.remove("refreshing");
      requestAnimationFrame(() => composer.classList.add("refreshing"));
    }
  } else if (data.personal_pending) {
    personalBlock.hidden = false;
    renderProfileCards($("personal-profile-cards"), data.profile_changes);
  } else {
    quietBlock.hidden = false;
    if (data.waiting.since) {
      $("quiet-title").textContent = "No draft in play";
      $("quiet-copy").textContent = "The last draft was discarded or sent separately. You can prepare a new one.";
      ensureQuietDraftButton();
    } else {
      $("quiet-title").textContent = "All caught up";
      $("quiet-copy").textContent = "The last client message has been answered.";
      removeQuietDraftButton();
    }
  }
}

function ensureQuietDraftButton() {
  if ($("quiet-draft-button")) return;
  const button = document.createElement("button");
  button.type = "button";
  button.id = "quiet-draft-button";
  button.className = "button button-secondary";
  button.textContent = "Draft a reply";
  button.addEventListener("click", draftAnyway);
  $("quiet-block").append(button);
}

function removeQuietDraftButton() {
  const button = $("quiet-draft-button");
  if (button) button.remove();
}

/* ---------------------------------------------------------------- actions */

async function saveEditIfNeeded() {
  if (!state.editing) return true;
  const text = $("draft-text").value.trim();
  if (!text) return false;
  const { ok } = await api(`/api/drafts/${state.thread.draft.id}/edit`, {
    method: "POST",
    body: JSON.stringify({ text }),
  });
  state.editing = false;
  return ok;
}

$("edit-button").addEventListener("click", async () => {
  if (state.editing) {
    await saveEditIfNeeded();
    await refreshThread();
  } else {
    state.editing = true;
    $("draft-text").readOnly = false;
    $("edit-button").textContent = "Done";
    $("edit-button").classList.add("active");
    $("draft-text").focus();
    $("draft-text").setSelectionRange($("draft-text").value.length, $("draft-text").value.length);
  }
});

$("regenerate-button").addEventListener("click", async () => {
  const button = $("regenerate-button");
  button.disabled = true;
  button.textContent = "Regenerating…";
  await api(`/api/drafts/${state.thread.draft.id}/regenerate`, { method: "POST" });
  button.textContent = "Regenerate";
  state.editing = false;
  state.ackArmed = false;
  await refreshThread();
});

$("discard-button").addEventListener("click", async () => {
  if (!window.confirm("Discard this draft? The inbound message stays open for a personal reply.")) return;
  await api(`/api/drafts/${state.thread.draft.id}/discard`, { method: "POST" });
  state.editing = false;
  await refreshThread();
});

async function sendDraft(acknowledge) {
  if (!(await saveEditIfNeeded())) return;
  const sendButton = $("send-button");
  sendButton.disabled = true;
  const { ok, status, body } = await api(`/api/drafts/${state.thread.draft.id}/approve`, {
    method: "POST",
    body: JSON.stringify(acknowledge ? { acknowledge_flags: true } : {}),
  });
  sendButton.disabled = false;
  if (!ok && status === 409 && body.error === "flags_require_acknowledgment") {
    state.ackArmed = true;
    state.thread.draft.flags = body.flags;
    renderFlags(state.thread.draft);
    return;
  }
  state.ackArmed = false;
  await refreshThread();
}

$("send-button").addEventListener("click", () => sendDraft(false));
$("ack-send-button").addEventListener("click", () => sendDraft(true));

async function draftAnyway() {
  await api(`/api/threads/${state.activeId}/draft`, { method: "POST" });
  await refreshThread();
}

$("draft-anyway-button").addEventListener("click", draftAnyway);

/* ------------------------------------------------------------ audit drawer */

$("history-panel").addEventListener("toggle", async () => {
  if (!$("history-panel").open || state.activeId === null) return;
  const { body } = await api(`/api/threads/${state.activeId}/audit`);
  const list = document.createElement("ol");
  (body.events || []).forEach((event) => {
    const item = document.createElement("li");
    const title = document.createElement("strong");
    title.textContent = event.event.replaceAll("_", " ");
    const meta = document.createElement("span");
    const detail = event.detail ? ` · ${JSON.stringify(event.detail)}` : "";
    meta.textContent = `${event.actor_type} · ${fmtAgo(event.occurred_at)} ago${detail}`;
    item.append(title, meta);
    list.append(item);
  });
  $("history-count").textContent = `${(body.events || []).length} events`;
  $("history-content").replaceChildren(list);
});

/* ------------------------------------------------------------------- boot */

$("advisor-avatar").textContent = initials(app.dataset.advisorName);
loadThreads();
setInterval(loadThreads, 30000);
