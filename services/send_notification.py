import smtplib
from email.mime.text import MIMEText

from sqlalchemy.orm import Session

from schema.send_notifications_DTO import SendNotificationDTO
from services.user_service import get_user


def send_notifications(db: Session, dto: SendNotificationDTO):
    users = get_user(db)

    sender = "info@aqua-powers.com"
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587

    subject = dto.subject
    body = dto.body

    password = "rxdm oabo eyct fzdb"

    try:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as s:
            s.starttls()
            s.login(sender, password)

            for user in users:
                recipient = user.email

                msg = MIMEText(body)
                msg['Subject'] = subject
                msg['From'] = sender
                msg['To'] = recipient

                s.sendmail(sender, recipient, msg.as_string())
                print(f"Email sent to {recipient}.")

    except Exception as e:
        print(f"Error sending email: {e}")
