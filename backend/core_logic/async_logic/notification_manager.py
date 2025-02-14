"""
TODO notify the frontend about a new system message.
"""



def send_notification(template_name, message="Test NOTIFICATION"):
    print("NOTIFICATION: %s" % message)
    from plyer import notification
    notification.notify(
        title=template_name,
        message=message,
        timeout=5,
    )
