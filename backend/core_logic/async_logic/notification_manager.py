"""
TODO notify the frontend about a new system message.
"""



def send_notification(template_name, message="Test NOTIFICATION"):
    print("NOTIFICATION: %s" % message)
    from plyer import notification
    notification.notify(
        title=sanitize_for_notification(template_name),
        message=sanitize_for_notification(message),
        timeout=5,
    )

def sanitize_for_notification(text):
    text = ''.join(e for e in text if e.isalnum() or e.isspace())
    if len(text) > 30:
        text = text[:30] + "..."

    return text
