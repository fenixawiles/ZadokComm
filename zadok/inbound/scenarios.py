"""Named synthetic scenarios, shared by the seed CLI, the simulator page, and
`flask inject`. One persona per feature the shell demonstrates."""
from __future__ import annotations

import uuid

from ..utils import now_iso

SCENARIOS: dict[str, dict] = {
    "alex_status_checkin": {
        "title": "Alex — status check-in (the owner's canonical case)",
        "from_email": "alex.morgan@example.com",
        "from_name": "Alex Morgan",
        "subject": "GMT-Master II",
        "body": "Hey Sarah — any luck with the GMT we talked about? If you've got one, I can come by this afternoon.",
    },
    "mia_appointment_with_profile_change": {
        "title": "Mia — appointment request + profile change",
        "from_email": "mia.chen@example.com",
        "from_name": "Mia Chen",
        "subject": "Saturday visit",
        "body": "Could I stop by Saturday to look at Datejust options? Late morning would be ideal if Elena is available. Also, my new number is (713) 555-0142.",
    },
    "daniel_complaint": {
        "title": "Daniel — complaint (routed for a personal reply)",
        "from_email": "daniel.ruiz@example.com",
        "from_name": "Daniel Ruiz",
        "subject": "Submariner follow-up",
        "body": "I've checked in three times about the Submariner and still haven't heard anything useful. Am I actually being considered or not?",
    },
    "jordan_new_prospect": {
        "title": "Jordan — unknown sender, new prospect",
        "from_email": "jordan.lee@example.com",
        "from_name": "Jordan Lee",
        "subject": "Steel Daytona",
        "body": "I'm looking for a steel Daytona. Do you have one available? I haven't shopped with you before but I'm ready to purchase.",
    },
    "casey_pleasantry": {
        "title": "Casey — pleasantry, short warm ack",
        "from_email": "casey.bennett@example.com",
        "from_name": "Casey Bennett",
        "subject": "Thank you",
        "body": "Hey Sarah, hope you're doing well — thanks again for everything!",
    },
    "policy_stress": {
        "title": "Victor — policy stress (draft violates on purpose)",
        "from_email": "victor.hale@example.com",
        "from_name": "Victor Hale",
        "subject": "Explorer II",
        "body": "Any update on the Explorer II? (demo: policy stress)",
    },
}


def build_payload(name: str, *, external_id: str | None = None, received_at: str | None = None,
                  source: str = "simulator") -> dict:
    scenario = SCENARIOS[name]
    return {
        "source": source,
        "external_message_id": external_id or f"{name}-{uuid.uuid4().hex[:10]}",
        "channel": "email",
        "from": {"email": scenario["from_email"], "name": scenario["from_name"]},
        "subject": scenario["subject"],
        "body": scenario["body"],
        "received_at": received_at or now_iso(),
    }
