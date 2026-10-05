import os


def send_missing_preparation_notification(
    *,
    booking_number,
    booked_by,
    missing_items,
):
    """
    Notify Admin that one or more samples were reported
    missing while preparing a booking.

    Email delivery is optional for the MVP. If no Admin
    email address is configured, the function returns
    without affecting the booking workflow.
    """

    admin_email = os.getenv("ADMIN_NOTIFICATION_EMAIL")

    if not admin_email:
        return {
            "sent": False,
            "reason": "ADMIN_NOTIFICATION_EMAIL not configured",
        }

    missing_lines = []

    for item in missing_items:
        sample_id = item["sample_id"]
        sample_name = item["sample_name"]
        note = item.get("missing_note") or "No note provided"

        missing_lines.append(
            (
                f"- {sample_id} — {sample_name}\n"
                f"  Note: {note}"
            )
        )

    missing_text = "\n".join(missing_lines)

    subject = (
        f"Missing sample during preparation — "
        f"{booking_number}"
    )

    body = f"""
Booking {booking_number} was prepared with one or more
missing samples.

Requested by:
{booked_by}

Missing samples:
{missing_text}

The remaining available samples have been prepared and
the booking is now Ready for Collection.

The missing samples require Admin follow-up.
""".strip()

    # Actual email provider will be connected here.
    #
    # For now we return the generated notification so
    # the booking workflow remains provider-independent.

    return {
        "sent": False,
        "reason": "Email provider not configured",
        "to": admin_email,
        "subject": subject,
        "body": body,
    }