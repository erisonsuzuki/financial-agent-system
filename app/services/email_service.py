import os
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr


def send_html_email(to_email: str, subject: str, html_body: str, text_body: str) -> None:
    smtp_server = os.getenv("SMTP_SERVER", "smtp-relay.brevo.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_login = os.getenv("SMTP_LOGIN")
    smtp_password = os.getenv("SMTP_KEY") or os.getenv("SMTP_PASSWORD")
    smtp_from_email = os.getenv("SMTP_FROM_EMAIL", os.getenv("SMTP_LOGIN", "no-reply@example.com"))
    smtp_from_name = os.getenv("SMTP_FROM_NAME", "Financial Agent System")
    smtp_timeout_seconds = int(os.getenv("SMTP_TIMEOUT_SECONDS", "10"))

    if not smtp_login or not smtp_password:
        raise RuntimeError("SMTP_LOGIN and SMTP_KEY are required to send emails")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = formataddr((smtp_from_name, smtp_from_email))
    message["To"] = to_email
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    tls_context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, smtp_port, timeout=smtp_timeout_seconds) as smtp:
        smtp.ehlo()
        smtp.starttls(context=tls_context)
        smtp.ehlo()
        smtp.login(smtp_login, smtp_password)
        smtp.send_message(message)
