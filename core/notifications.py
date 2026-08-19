import logging

import requests

logger = logging.getLogger(__name__)


def send_notifications(tokens, title, body):
    # sound: "default" makes iOS actually buzz/chime; without it the notification
    # arrives silently in Notification Center.
    messages = [
        {"to": token, "title": title, "body": body, "sound": "default", "priority": "high"}
        for token in tokens
    ]

    # Chunk in 100s
    for i in range(0, len(messages), 100):
        try:
            r = requests.post("https://exp.host/--/api/v2/push/send", json=messages[i : i + 100], timeout=20)
        except requests.RequestException as e:
            logger.error("expo push send failed: %s", e)
            continue

        if not r.ok:
            logger.error("expo push send failed: HTTP %s %s", r.status_code, r.text[:300])
            continue
            # TODO: Implement retry logic

        try:
            tickets = r.json().get("data", [])
        except ValueError:
            tickets = []
        errors = [t for t in tickets if isinstance(t, dict) and t.get("status") != "ok"]
        if errors:
            logger.error("expo push ticket errors (%d of %d): %s", len(errors), len(tickets), errors[:5])

    # TODO: Implement checking push receipts after 15 mins
