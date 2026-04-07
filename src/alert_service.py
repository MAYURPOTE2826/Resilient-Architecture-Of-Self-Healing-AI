import os
import smtplib
import ssl
import threading
from email.message import EmailMessage

from dotenv import load_dotenv
from logger import logger

load_dotenv()

SMTP_SERVER     = "smtp.gmail.com"
SMTP_PORT       = 587
SMTP_TIMEOUT    = 10   # seconds — prevents indefinite block on unreachable server

SENDER_EMAIL    = os.getenv("SENDER_EMAIL", "")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")
ADMIN_EMAIL     = os.getenv("ADMIN_EMAIL", "")


def _send(subject: str, message: str) -> None:
    """Internal blocking send — always called from a background thread."""
    try:
        msg = EmailMessage()
        msg["From"]    = SENDER_EMAIL
        msg["To"]      = ADMIN_EMAIL
        msg["Subject"] = subject
        msg.set_content(message)

        # Explicit TLS context verifies server certificate — prevents MITM attacks
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=SMTP_TIMEOUT) as server:
            server.starttls(context=context)
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        logger.info("Alert email sent to admin")

    except smtplib.SMTPAuthenticationError:
        logger.error("Alert failed: invalid SMTP credentials")
    except smtplib.SMTPException as e:
        logger.error(f"Alert failed (SMTP error): {e}")
    except OSError as e:
        logger.error(f"Alert failed (network/timeout error): {e}")


def send_alert(subject: str, message: str) -> None:
    """Fire-and-forget alert — never blocks the calling thread."""
    if not SENDER_PASSWORD:
        logger.warning("Alert skipped: SENDER_PASSWORD not set in environment")
        return

    threading.Thread(target=_send, args=(subject, message), daemon=True).start()
