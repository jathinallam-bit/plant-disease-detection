# email_service.py
from flask_mail import Mail, Message

def send_alert_email(user_email, disease, severity):
    """Send email alert when disease detected"""
    if severity in ['HIGH', 'MEDIUM']:
        msg = Message(
            '⚠️ Plant Disease Alert',
            recipients=[user_email],
            body=f'Your plant has been diagnosed with {disease} (Severity: {severity}). Please take action immediately.'
        )
        mail.send(msg)