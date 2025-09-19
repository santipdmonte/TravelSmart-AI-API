from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl
import os
import certifi


email_router = APIRouter(prefix="/auth/email")

# Email settings (example with Gmail SMTP)
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_REPLY_TO = os.getenv("SMTP_REPLY_TO")
EMAIL_TOKEN_EXPIRE_MINUTES = int(os.getenv("EMAIL_TOKEN_EXPIRE_MINUTES"))
URL = os.getenv("URL")

def send_verification_email(email: str, token: str):
    try:
        # Create the email content (plain + HTML alternative)
        message = MIMEMultipart("alternative")
        message["From"] = SMTP_USER
        message["To"] = email
        message["Subject"] = f"Welcome! Click the button to login"
        message["Reply-To"] = SMTP_REPLY_TO

        verification_link = f"{URL}/auth/verify-token/?token={token}"

        # Plain text fallback
        plain_text_body = verification_link

        # HTML body from template with link substitution
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            template_path = os.path.join(base_dir, "static", "template", "magic-link.html")
            with open(template_path, "r", encoding="utf-8") as f:
                html_template = f.read()
            html_body = html_template.replace("{{ link }}", verification_link)
        except Exception:
            # Fallback minimal HTML if template missing/unreadable
            html_body = (
                f"<html><body>"
                f"<p>Click the button or link to continue:</p>"
                f"<p><a href=\"{verification_link}\" target=\"_blank\" rel=\"noopener noreferrer\">Enter</a></p>"
                f"<p>{verification_link}</p>"
                f"</body></html>"
            )

        message.attach(MIMEText(plain_text_body, "plain"))
        message.attach(MIMEText(html_body, "html"))

        # Connect to SMTP server
        context = ssl.create_default_context(cafile=certifi.where())
        server = smtplib.SMTP(SMTP_SERVER, int(SMTP_PORT) if SMTP_PORT else 587)
        server.starttls(context=context)
        server.login(SMTP_USER, SMTP_PASSWORD)

        # Send email
        server.sendmail(SMTP_USER, email, message.as_string())
        server.quit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email failed: {str(e)}")