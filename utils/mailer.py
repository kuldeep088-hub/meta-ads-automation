import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from utils.logger import get_logger
import config

log = get_logger("mailer")


def send_email_alert(
    to_email: str,
    alert_type: str,
    campaign_name: str,
    message: str,
    actual_value: float = 0.0,
    threshold_value: float = 0.0,
) -> bool:
    if not all([config.SMTP_USER, config.SMTP_PASS, to_email]):
        log.warning("Email alert skipped  -  SMTP credentials or recipient not configured.")
        return False

    subject = f"[META ADS ALERT] {alert_type.upper()}  -  {campaign_name}"
    body = f"""
Meta Ads Automation Alert
==========================
Alert Type : {alert_type}
Campaign   : {campaign_name}
Time       : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Details
-------
{message}

Actual Value    : {actual_value:.4f}
Threshold Value : {threshold_value:.4f}

Please review your campaign in Meta Ads Manager.

--
Sent by Meta Ads Automation
""".strip()

    msg = MIMEMultipart()
    msg["From"] = config.SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
            server.ehlo()
            server.starttls(context=context)
            server.login(config.SMTP_USER, config.SMTP_PASS)
            server.sendmail(config.SMTP_USER, to_email, msg.as_string())
        log.info(f"Alert email sent to {to_email}: {alert_type}")
        return True
    except Exception as e:
        log.error(f"Failed to send alert email: {e}")
        return False
