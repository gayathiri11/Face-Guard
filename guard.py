import cv2
import os
import time
import socket
import shutil
import smtplib
import threading
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from config import (EMAIL_SENDER, EMAIL_PASSWORD,
                    EMAIL_RECEIVER, ACCESS_OTP, MAX_SCANS)

# ─── Folders ─────────────────────────────────────────────
os.makedirs("alerts_log", exist_ok=True)
os.makedirs("sent_log", exist_ok=True)

# ─── Internet Check ──────────────────────────────────────
def is_connected():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except:
        return False
# ─── Get IP Location ─────────────────────────────────────
def get_location():
    try:
        import requests
        # Try multiple location APIs for accuracy
        response = requests.get(
            "http://ip-api.com/json/?fields=status,city,"
            "regionName,country,isp,query,lat,lon",
            timeout=5
        )
        data = response.json()
        if data["status"] == "success":
            location = f"""
📍 Approximate Location (IP Based):
City     : {data['city']}
Region   : {data['regionName']}
Country  : {data['country']}
ISP      : {data['isp']}
IP       : {data['query']}
Maps     : https://maps.google.com/?q={data['lat']},{data['lon']}

⚠️ Note: Location is ISP based — may vary slightly
            """
            return location
        return "📍 Location: Could not fetch"
    except:
        return "📍 Location: No internet"

# ─── Send Alert Email to OWNER with Allow/Deny OTP ───────
def send_owner_alert(image_path, timestamp):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER
        msg["Subject"] = "⚠️ FaceGuard — Unknown Person Trying to Access Your Laptop!"

        body = f"""
FaceGuard Security Alert!

An unknown person tried to access your laptop.

Time     : {timestamp}
Device   : {os.environ.get('COMPUTERNAME', 'Unknown')}
{get_location()}

The person's photo is attached below.

To GRANT access  → Share OTP: {ACCESS_OTP} with them
To DENY access   → Do nothing. Screen will auto lock in 60 seconds.
        """
        msg.attach(MIMEText(body, "plain"))

        if image_path and os.path.exists(image_path):
            with open(image_path, "rb") as f:
                msg.attach(MIMEImage(f.read()))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER,
                          msg.as_string())
        print("✅ Owner alert sent!")
        return True
    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False

# ─── Save Alert Locally ──────────────────────────────────
def save_alert_locally(image_path, timestamp):
    filename = f"alerts_log/alert_{timestamp}.jpg"
    if image_path and os.path.exists(image_path):
        shutil.copy(image_path, filename)
    with open("alerts_log/log.txt", "a") as f:
        f.write(f"{timestamp} | Unknown Access | {filename}\n")
    return filename

# ─── OTP Popup for Unknown User ──────────────────────────
def show_otp_popup():
    result = [False]

    popup = tk.Toplevel()
    popup.title("🔐 Access Required")
    popup.geometry("380x280")
    popup.configure(bg="#0A0A2E")
    popup.resizable(False, False)
    popup.grab_set()

    tk.Label(popup,
             text="🚨 Access Denied",
             font=("Helvetica", 18, "bold"),
             bg="#0A0A2E", fg="#FF4444").pack(pady=15)

    tk.Label(popup,
             text="Your face is not recognized.\nOwner has been notified with your photo.\n\nIf owner grants access, enter OTP below:",
             font=("Helvetica", 10),
             bg="#0A0A2E", fg="white",
             justify="center").pack(pady=5)

    otp_entry = tk.Entry(popup,
                         font=("Helvetica", 16, "bold"),
                         width=12, bg="#12122E", fg="white",
                         insertbackground="white",
                         show="*", justify="center")
    otp_entry.pack(pady=10)

    status_lbl = tk.Label(popup, text="",
                          font=("Helvetica", 11, "bold"),
                          bg="#0A0A2E", fg="yellow")
    status_lbl.pack()

    def verify():
        if otp_entry.get().strip() == ACCESS_OTP:
            result[0] = True
            status_lbl.config(text="✅ Access Granted! Welcome!",
                            fg="#00FF88")
            popup.after(2000, popup.destroy)
        else:
            status_lbl.config(text="❌ Wrong OTP! Locking screen...",
                            fg="red")
            popup.after(2000, lambda: [
                popup.destroy(),
                os.system("rundll32.exe user32.dll,LockWorkStation")
            ])

    tk.Button(popup,
              text="🔓 Verify OTP",
              font=("Helvetica", 12, "bold"),
              bg="#00D4FF", fg="#0A0A2E",
              width=15,
              command=verify).pack(pady=8)

    # Countdown timer
    timer_lbl = tk.Label(popup,
                         text="Auto-lock in: 60s",
                         font=("Helvetica", 9),
                         bg="#0A0A2E", fg="#A0A8C0")
    timer_lbl.pack()

    def countdown(n):
        if n > 0 and popup.winfo_exists():
            timer_lbl.config(text=f"Auto-lock in: {n}s")
            popup.after(1000, countdown, n-1)
        elif popup.winfo_exists() and not result[0]:
            popup.destroy()
            os.system("rundll32.exe user32.dll,LockWorkStation")

    countdown(60)
    popup.wait_window()
    return result[0]

# ─── Face Detection Setup ────────────────────────────────
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades +
    'haarcascade_frontalface_default.xml'
)

def load_known_face():
    for file in os.listdir("known_face"):
        path = os.path.join("known_face", file)
        img = cv2.imread(path)
        if img is not None:
            return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return None

def get_face_score(known_gray, frame_gray, faces):
    x, y, w, h = faces[0]
    face_crop = frame_gray[y:y+h, x:x+w]
    face_resized = cv2.resize(face_crop, (200, 200))

    known_detected = face_cascade.detectMultiScale(
        known_gray, 1.1, 3, minSize=(30, 30))
    if len(known_detected) > 0:
        kx, ky, kw, kh = known_detected[0]
        known_crop = known_gray[ky:ky+kh, kx:kx+kw]
        known_resized = cv2.resize(known_crop, (200, 200))
    else:
        known_resized = cv2.resize(known_gray, (200, 200))

    h1 = cv2.calcHist([known_resized], [0], None, [256], [0, 256])
    h2 = cv2.calcHist([face_resized], [0], None, [256], [0, 256])
    return cv2.compareHist(h1, h2, cv2.HISTCMP_CORREL)

# ─── Main FaceGuard Logic ────────────────────────────────
def run_faceguard(root, status_label):

    def update(text, color):
        status_label.config(text=text, fg=color)

    known_gray = load_known_face()
    if known_gray is None:
        update("❌ No face registered!", "red")
        return

    # ── Step 1: Ask to turn on camera ─────────────────
    update("📷 Please turn on your camera...", "#00D4FF")
    root.update()

    confirm = messagebox.askyesno(
        "FaceGuard 🛡️",
        "Turn on camera for face verification?\n\n"
        "This keeps your laptop secure!"
    )
    if not confirm:
        update("⚠️ Camera skipped — not protected!", "orange")
        return

    # ── Step 2: Start camera, scan MAX_SCANS times ────
    cam = cv2.VideoCapture(0)
    time.sleep(1)
    update("👀 Scanning face...", "yellow")
    root.update()

    scores = []
    scan_count = 0
    last_frame = None

    while scan_count < MAX_SCANS:
        ret, frame = cam.read()
        if not ret:
            continue

        last_frame = frame.copy()
        cv2.imshow("FaceGuard — Scanning...", frame)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray, 1.1, 3, minSize=(30, 30))

        if len(faces) > 0:
            score = get_face_score(known_gray, gray, faces)
            scores.append(score)
            scan_count += 1
            update(f"👀 Scanning... {scan_count}/{MAX_SCANS}", "yellow")
            root.update()
            print(f"Scan {scan_count}: {score:.3f}")

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        time.sleep(0.5)

    cam.release()
    cv2.destroyAllWindows()

    # ── Step 3: Decide authorized or not ─────────────
    if not scores:
        update("⚠️ No face detected! Try again.", "orange")
        return

    avg = sum(scores) / len(scores)
    print(f"Final Average Score: {avg:.3f}")

    # ── Step 4: AUTHORIZED ────────────────────────────
    if avg > 0.60:
        update("✅ Welcome! You're verified!", "#00FF88")
        root.update()

        # Notify owner to turn off camera for privacy
        messagebox.showinfo(
            "✅ Access Granted — FaceGuard",
            "Welcome! You're verified ✅\n\n"
            "🔒 You can now turn off your camera\n"
            "for privacy — you're all set!"
        )
        update("🔒 Camera off — Stay Safe!", "#00FF88")

    # ── Step 5: UNKNOWN FACE ──────────────────────────
    else:
        update("🚨 Unknown Face Detected!", "red")
        root.update()

        # Save intruder photo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_path = f"temp_{timestamp}.jpg"
        if last_frame is not None:
            cv2.imwrite(temp_path, last_frame)

        saved = save_alert_locally(temp_path, timestamp)

        # Send alert to owner
        if is_connected():
            update("📤 Notifying owner...", "orange")
            root.update()
            threading.Thread(
                target=send_owner_alert,
                args=(saved, timestamp),
                daemon=True
            ).start()
            
        else:
            update("📵 Offline — alert saved locally!", "orange")
            root.update()

        if os.path.exists(temp_path):
            os.remove(temp_path)

        # Show OTP popup for unknown user
        update("⏳ Waiting for owner approval...", "orange")
        root.update()
        granted = show_otp_popup()

        if granted:
            update("✅ Access Granted by Owner!", "#00FF88")
        else:
            update("🔒 Access Denied — Locking!", "red")

# ─── Camera On/Off Popup ─────────────────────────────────
def ask_camera_off():
    messagebox.showinfo(
        "🔒 Privacy — FaceGuard",
        "Verification complete!\n\n"
        "Please turn OFF your camera now\n"
        "to protect your privacy. 🔒"
    )

# ─── Main UI ─────────────────────────────────────────────
def start_gui():
    root = tk.Tk()
    root.title("FaceGuard 🛡️")
    root.geometry("420x320")
    root.configure(bg="#0A0A2E")
    root.resizable(False, False)

    tk.Label(root,
             text="🛡️ FaceGuard",
             font=("Helvetica", 28, "bold"),
             bg="#0A0A2E", fg="white").pack(pady=15)

    tk.Label(root,
             text="AI-Powered Laptop Security",
             font=("Helvetica", 12),
             bg="#0A0A2E", fg="#00D4FF").pack()

    status_label = tk.Label(root,
                            text="⏳ Click Start to begin...",
                            font=("Helvetica", 13, "bold"),
                            bg="#0A0A2E", fg="yellow")
    status_label.pack(pady=20)

    def on_start():
        start_btn.config(state="disabled")
        threading.Thread(
            target=run_faceguard,
            args=(root, status_label),
            daemon=True
        ).start()

    start_btn = tk.Button(root,
                          text="🚀 Start FaceGuard",
                          font=("Helvetica", 13, "bold"),
                          bg="#00D4FF", fg="#0A0A2E",
                          width=20, height=2,
                          command=on_start)
    start_btn.pack(pady=10)

    tk.Label(root,
             text="Scans face 6 times for accuracy",
             font=("Helvetica", 9),
             bg="#0A0A2E", fg="#A0A8C0").pack()

    root.mainloop()

# ─── Run ─────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        from PIL import Image, ImageTk
    except:
        os.system("pip install Pillow")
    start_gui()