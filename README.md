# Zadok Client Communication Concept Demo

This repository contains a self-contained, synthetic demonstration of an embedded CRM communication workflow for a luxury jewelry retailer.

It is intentionally not presented as a separate SaaS product. The demo focuses on one operational problem: helping busy client advisors respond to inbound messages without leaving their existing conversation thread.

## Demonstrated workflow

1. An inbound client email appears in the mock CRM conversation.
2. A proposed response is already present when the advisor opens the thread.
3. Approved relationship context influences the response silently.
4. The advisor can Send, Edit, or Regenerate without leaving the thread.
5. Appointment availability is used only when the inbound message is actually requesting a visit.

The interface includes product, complaint, scheduling, and first-time-customer conversations to demonstrate intent-sensitive planning.

All names, records, messages, availability, policies, and appointment times are fictional. Nothing in the demo connects to Zadok, Salesforce, Woven, a calendar, inventory, or a messaging system.

## Run locally

Serve the `dist` directory with any static web server, then open the local URL in a browser.
