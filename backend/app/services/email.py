"""
Email notification service supporting SMTP provider and development outbox recording.
"""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("returnpilot.email")

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM", "no-reply@returnpilot.ai")
SMTP_TLS = os.getenv("SMTP_TLS", "true").lower() in ("true", "1", "yes")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# In-memory storage for development/test email inspection
dev_outbox: List[Dict[str, str]] = []


def is_smtp_configured() -> bool:
    """Checks whether live SMTP credentials are fully provided."""
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)


def send_email(
    to_email: str,
    subject: str,
    body_text: str,
    body_html: str,
) -> Tuple[bool, str]:
    """
    Sends an email via configured SMTP server.
    If SMTP is not configured, records to dev_outbox without claiming live delivery.
    Returns (delivered_via_provider: bool, status_message: str).
    """
    if not is_smtp_configured():
        # Record in development outbox
        dev_outbox.append({
            "to": to_email,
            "subject": subject,
            "body_text": body_text,
            "body_html": body_html,
        })
        logger.info(f"[DEV EMAIL OUTBOX] Email recorded for {to_email}: {subject}")
        return False, "SMTP provider not configured. Recorded in development outbox."

    # Live SMTP delivery
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_FROM
        msg["To"] = to_email

        part1 = MIMEText(body_text, "plain")
        part2 = MIMEText(body_html, "html")
        msg.attach(part1)
        msg.attach(part2)

        if SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10)
        else:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
            if SMTP_TLS:
                server.starttls()

        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM, [to_email], msg.as_string())
        server.quit()
        return True, "Email sent successfully via SMTP provider."
    except Exception as e:
        logger.error(f"SMTP delivery failed to {to_email}: {e}")
        return False, f"SMTP delivery failed: {str(e)}"


def send_verification_email(to_email: str, full_name: str, raw_token: str) -> Tuple[bool, str]:
    """Sends an email verification link and token to the user."""
    verify_url = f"{FRONTEND_URL}/verify-email?token={raw_token}&email={to_email}"
    subject = "Verify your ReturnPilot AI account"

    body_text = f"""Hello {full_name},

Thank you for registering with ReturnPilot AI.
Please verify your email address to activate your account:

{verify_url}

Your verification token:
{raw_token}

This token will expire in 30 minutes. If you did not create this account, please ignore this email.
"""

    body_html = f"""<!DOCTYPE html>
<html>
<body style="font-family: Inter, -apple-system, sans-serif; background-color: #f8fafc; padding: 24px; color: #0f172a;">
  <div style="max-width: 540px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 32px;">
    <h2 style="color: #4f46e5; margin-top: 0;">ReturnPilot AI</h2>
    <h3 style="margin-top: 16px;">Verify your email address</h3>
    <p>Hello {full_name},</p>
    <p>Please confirm your email address to complete your registration and access the ReturnPilot AI dashboard.</p>
    <div style="margin: 24px 0;">
      <a href="{verify_url}" style="background-color: #4f46e5; color: #ffffff; padding: 12px 24px; border-radius: 10px; text-decoration: none; font-weight: 600; display: inline-block;">Verify Email Address</a>
    </div>
    <p style="color: #64748b; font-size: 13px;">Or copy and paste this verification token into the verification page:</p>
    <div style="background-color: #f1f5f9; padding: 12px; border-radius: 8px; font-family: monospace; font-size: 14px; word-break: break-all;">
      {raw_token}
    </div>
    <p style="color: #94a3b8; font-size: 12px; margin-top: 24px;">This verification link will expire in 30 minutes. If you did not create an account, you can safely ignore this email.</p>
  </div>
</body>
</html>
"""
    return send_email(to_email, subject, body_text, body_html)


def send_password_reset_email(to_email: str, full_name: str, raw_token: str) -> Tuple[bool, str]:
    """Sends a password reset link and token to the user."""
    reset_url = f"{FRONTEND_URL}/reset-password?token={raw_token}"
    subject = "Reset your ReturnPilot AI password"

    body_text = f"""Hello {full_name},

A password reset request was received for your ReturnPilot AI account.
To reset your password, visit the following link:

{reset_url}

Your reset token:
{raw_token}

This token will expire in 15 minutes. If you did not request a password reset, please ignore this email.
"""

    body_html = f"""<!DOCTYPE html>
<html>
<body style="font-family: Inter, -apple-system, sans-serif; background-color: #f8fafc; padding: 24px; color: #0f172a;">
  <div style="max-width: 540px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 32px;">
    <h2 style="color: #4f46e5; margin-top: 0;">ReturnPilot AI</h2>
    <h3 style="margin-top: 16px;">Password Reset Request</h3>
    <p>Hello {full_name},</p>
    <p>We received a request to reset your password. Click the button below to choose a new password:</p>
    <div style="margin: 24px 0;">
      <a href="{reset_url}" style="background-color: #4f46e5; color: #ffffff; padding: 12px 24px; border-radius: 10px; text-decoration: none; font-weight: 600; display: inline-block;">Reset Password</a>
    </div>
    <p style="color: #64748b; font-size: 13px;">Or copy and paste this reset token:</p>
    <div style="background-color: #f1f5f9; padding: 12px; border-radius: 8px; font-family: monospace; font-size: 14px; word-break: break-all;">
      {raw_token}
    </div>
    <p style="color: #94a3b8; font-size: 12px; margin-top: 24px;">This link expires in 15 minutes. If you did not request this, please ignore this email.</p>
  </div>
</body>
</html>
"""
    return send_email(to_email, subject, body_text, body_html)
