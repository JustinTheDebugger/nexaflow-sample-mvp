import os

from dotenv import load_dotenv
from services.email_service import deliver_email

load_dotenv()

recipient = os.getenv("ADMIN_NOTIFICATION_EMAIL")

if not recipient:
    raise ValueError("ADMIN_NOTIFICATION_EMAIL is not configured.")

result = deliver_email(
    to=recipient,
    subject="NexaFlow - Email Delivery Test",
    body=(
        "This is a test email from NexaFlow.\n\n"
        "Email delivery has been configured successfully."
    ),
)

print("Email submitted successfully.")
print(result)