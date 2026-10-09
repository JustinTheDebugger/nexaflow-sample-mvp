import os
from pathlib import Path

import resend
from dotenv import load_dotenv

# Load .env from the NexaFlow project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")


def deliver_email(*, to, subject, body):
    """
    Send a transactional email through Resend.

    Returns delivery submission information.
    Raises an exception if the provider rejects the request.
    """

    api_key = os.getenv("RESEND_API_KEY")
    sender = os.getenv("NEXAFLOW_FROM_EMAIL")

    if not api_key:
        raise ValueError("RESEND_API_KEY is not configured.")

    if not sender:
        raise ValueError("NEXAFLOW_FROM_EMAIL is not configured.")

    resend.api_key = api_key

    response = resend.Emails.send({
        "from": sender,
        "to": [to],
        "subject": subject,
        "text": body,
    })

    return {
        "sent": True,
        "provider": "resend",
        "provider_response": response,
    }

def _format_sample_items(items):
    """Format sample records for notification emails."""
    lines = []

    for item in items:
        sample_id = item.get("sample_id", "Unknown")
        sample_name = item.get("sample_name", "Unnamed Sample")
        lines.append(f"- {sample_id}: {sample_name}")

    return "\n".join(lines) if lines else "None"


def send_missing_preparation_notification(
    *,
    booking_number,
    booked_by,
    missing_items,
):
    """Notify Admin when samples are reported missing."""

    if not missing_items:
        return {"sent": False, "reason": "No missing samples"}

    recipient = os.getenv("ADMIN_NOTIFICATION_EMAIL")

    if not recipient:
        raise ValueError("ADMIN_NOTIFICATION_EMAIL is not configured.")

    subject = f"[NexaFlow] Missing Samples - {booking_number}"

    body = f"""NexaFlow - Missing Sample Alert

Booking: {booking_number}
Requested by: {booked_by}

The following samples were reported missing during preparation:

{_format_sample_items(missing_items)}

Please investigate the missing samples in NexaFlow.

This is an automated notification.
"""

    return deliver_email(
        to=recipient,
        subject=subject,
        body=body,
    )


def send_ready_for_collection_notification(
    *,
    booking_number,
    booked_by,
    prepared_items,
    exception_items=None,
):
    """Notify the requester when samples are ready for collection."""

    if not prepared_items:
        return {"sent": False, "reason": "No prepared samples"}

    recipient = os.getenv("REQUESTER_NOTIFICATION_EMAIL")

    if not recipient:
        raise ValueError("REQUESTER_NOTIFICATION_EMAIL is not configured.")

    subject = f"[NexaFlow] Ready for Collection - {booking_number}"

    exceptions = _format_sample_items(exception_items or [])

    body = f"""NexaFlow - Samples Ready for Collection

Booking: {booking_number}
Requested by: {booked_by}

The following samples are ready for collection:

{_format_sample_items(prepared_items)}

Collection location: C1 - Collection/Dispatch Area

Items not supplied:
{exceptions}

Please collect your samples and complete checkout.

This is an automated notification.
"""

    return deliver_email(
        to=recipient,
        subject=subject,
        body=body,
    )