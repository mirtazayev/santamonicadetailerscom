import smtplib
from email.mime.text import MIMEText

from fastapi import HTTPException


def send_email(name: str, email: str, phone: str, message: str):
    sender_email = "info@aqua-powers.com"
    sender_password = "rxdm oabo eyct fzdb"
    admin_email = "abduqodirovabdulloh2005@gmail.com"

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)

            # Email to admin
            admin_msg = MIMEText(
                f"Name: {name}\nEmail: {email}\nPhone: {phone}\nMessage: {message}"
            )
            admin_msg['Subject'] = f'New Contact Form Submission ({phone})'
            admin_msg['From'] = sender_email
            admin_msg['To'] = admin_email

            server.sendmail(sender_email, admin_email, admin_msg.as_string())

            # Email to user
            user_msg = MIMEText(
                f"Hi {name},\n\n"
                f"Thanks for reaching out to Santa Monica Detailers. We’ve received your message and are excited about your interest "
                f"in our services. Our team will contact you soon to assist.\n"
                f"If you have urgent questions, feel free to call us at +1 309 262 9545.\n\n"
                f"Best regards,\n"
                f"The Santa Monica Detailers Team"
            )
            user_msg['Subject'] = 'Thank You for Contacting Santa Monica Detailers!'
            user_msg['From'] = sender_email
            user_msg['To'] = email

            server.sendmail(sender_email, email, user_msg.as_string())

        return {"message": "Emails sent successfully!"}

    except smtplib.SMTPException as e:
        raise HTTPException(status_code=500, detail=f"Error sending email: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
