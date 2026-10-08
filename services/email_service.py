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