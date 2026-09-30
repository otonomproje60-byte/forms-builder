"""
Notification services for Forms Builder (email and webhook).
"""
import asyncio
import logging
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib
import httpx

from models import Form, FormSubmission
from config import settings

logger = logging.getLogger(__name__)


async def send_email_notification(
    form: Form,
    submission: FormSubmission,
    form_data: dict,
) -> bool:
    """
    Send email notification for a new form submission.

    Args:
        form: The form that was submitted
        submission: The submission record
        form_data: The raw form data submitted

    Returns:
        True if sent successfully, False otherwise
    """
    if not form.email_enabled or not form.email_to:
        return True  # No email configured, not an error

    if not settings.SMTP_ENABLED or not settings.SMTP_HOST:
        logger.warning("SMTP not configured, skipping email notification")
        return False

    try:
        # Build email content
        subject = form.email_subject or f"New submission: {form.name}"
        
        # Create HTML body
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2>New Form Submission</h2>
            <p><strong>Form:</strong> {form.name}</p>
            <p><strong>Submitted at:</strong> {submission.submitted_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            <p><strong>Submission ID:</strong> {submission.id}</p>
            
            <h3>Submitted Data:</h3>
            <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
        """
        
        for field_name, field_value in form_data.items():
            if field_name == form.honeypot_field_name:
                continue  # Skip honeypot field in email
            html_body += f"""
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold; width: 30%;">{field_name}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{field_value}</td>
                </tr>
            """
        
        html_body += """
            </table>
            <hr style="margin: 20px 0;">
            <p style="font-size: 12px; color: #888;">
                This email was sent from Forms Builder.
            </p>
        </body>
        </html>
        """

        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = settings.SMTP_FROM
        message["To"] = form.email_to
        message.attach(MIMEText(html_body, "html"))

        # Send email
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER if settings.SMTP_USER else None,
            password=settings.SMTP_PASSWORD if settings.SMTP_PASSWORD else None,
            use_tls=settings.SMTP_TLS,
        )

        logger.info(f"Email notification sent for submission {submission.id} to {form.email_to}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email notification: {e}")
        return False


async def send_webhook_notification(
    form: Form,
    submission: FormSubmission,
    form_data: dict,
) -> bool:
    """
    Send webhook notification for a new form submission.

    Args:
        form: The form that was submitted
        submission: The submission record
        form_data: The raw form data submitted

    Returns:
        True if sent successfully, False otherwise
    """
    if not form.webhook_enabled or not form.webhook_url:
        return True  # No webhook configured, not an error

    if not settings.WEBHOOK_ENABLED:
        logger.warning("Webhooks disabled, skipping webhook notification")
        return False

    # Prepare payload
    payload = {
        "event": "form.submission",
        "form": {
            "id": form.id,
            "name": form.name,
        },
        "submission": {
            "id": submission.id,
            "data": form_data,
            "submitted_at": submission.submitted_at.isoformat(),
            "client_ip": submission.client_ip,
        },
    }

    # Add honeypot info
    if form.honeypot_enabled:
        payload["submission"]["honeypot_field"] = form.honeypot_field_name
        payload["submission"]["honeypot_triggered"] = submission.honeypot_triggered

    # Send with retries
    headers = {"Content-Type": "application/json"}
    if form.webhook_secret:
        import hmac
        import hashlib
        import json
        signature = hmac.new(
            form.webhook_secret.encode(),
            json.dumps(payload).encode(),
            hashlib.sha256
        ).hexdigest()
        headers["X-Forms-Signature"] = f"sha256={signature}"

    for attempt in range(settings.WEBHOOK_MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=settings.WEBHOOK_TIMEOUT) as client:
                response = await client.post(
                    form.webhook_url,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                logger.info(f"Webhook notification sent for submission {submission.id} to {form.webhook_url}")
                return True

        except httpx.TimeoutException:
            logger.warning(f"Webhook timeout (attempt {attempt + 1}/{settings.WEBHOOK_MAX_RETRIES})")
        except httpx.HTTPStatusError as e:
            logger.warning(f"Webhook HTTP error {e.response.status_code} (attempt {attempt + 1}/{settings.WEBHOOK_MAX_RETRIES})")
        except Exception as e:
            logger.error(f"Webhook error: {e}")

        if attempt < settings.WEBHOOK_MAX_RETRIES - 1:
            await asyncio.sleep(settings.WEBHOOK_RETRY_DELAY)

    logger.error(f"Webhook notification failed after {settings.WEBHOOK_MAX_RETRIES} attempts")
    return False


async def send_notifications(
    form: Form,
    submission: FormSubmission,
    form_data: dict,
) -> None:
    """
    Send all configured notifications for a form submission.
    Runs email and webhook concurrently.

    Args:
        form: The form that was submitted
        submission: The submission record
        form_data: The raw form data submitted
    """
    tasks = []

    if form.email_enabled and form.email_to:
        tasks.append(send_email_notification(form, submission, form_data))

    if form.webhook_enabled and form.webhook_url:
        tasks.append(send_webhook_notification(form, submission, form_data))

    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Notification task {i} failed: {result}")