import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime
from config import EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER

def send_alert(image_path):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = "⚠️ FaceGuard Alert - Unknown Person Detected!"

    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    body = f"Unknown face detected on your laptop at {time_now}. Photo attached."
    msg.attach(MIMEText(body, "plain"))

    with open(image_path, "rb") as f:
        img = MIMEImage(f.read())
        msg.attach(img)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
    
    print("Alert email sent ✅")