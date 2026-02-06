import smtplib
from email.message import EmailMessage

# ====== CONFIGURATION ======
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

SENDER_EMAIL = "potemayur2826@gmail.com"
SENDER_PASSWORD = "xevx fkgj nyyz tirq"  # Gmail App Password
ADMIN_EMAIL = "mayurpote6963@gmail.com"
# ===========================

def send_alert(subject, message):
    try:
        msg = EmailMessage()
        msg["From"] = SENDER_EMAIL
        msg["To"] = ADMIN_EMAIL
        msg["Subject"] = subject
        msg.set_content(message)

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()

        print("📧 Alert email sent to admin")

    except Exception as e:
        print("❌ Failed to send alert:", e)
