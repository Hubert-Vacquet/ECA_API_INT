import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import Config

def send_verification_code(email: str, code: str):
    sender_email = "ton_adresse_mail@example.com"
    receiver_email = email
    subject = "Votre code de vérification"
    body = f"Votre code de vérification est : {code}"

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.example.com", 587) as server:
            server.starttls()
            server.login(sender_email, Config.PASSWORD_SRV_MAIL)
            server.sendmail(sender_email, receiver_email, message.as_string())
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'e-mail : {e}")
        raise
