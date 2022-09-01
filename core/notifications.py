import requests


def send_notifications(tokens, title, body):
    messages = [{"to": token, "title": title, "body": body} for token in tokens]

    # Chunk in 100s
    for i in range(0, len(messages), 100):
        r = requests.post("https://exp.host/--/api/v2/push/send", json=messages[i : i + 100])

        if not r.ok:
            pass
            # TODO: Implement retry logic

    # TODO: Implement checking push receipts after 15 mins
