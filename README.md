# 🛡️ FaceGuard — AI Laptop Security System

An AI-powered lightweight laptop security system 
that uses face recognition to protect your laptop 
from unauthorized access.

## 🚨 Problem
Students and professionals leave laptops unattended 
in colleges, libraries, hostels and cafes. Normal 
passwords don't help once laptop is already open — 
there's no way to know WHO accessed it or WHEN.

## 💡 Solution
FaceGuard silently monitors the webcam and instantly 
alerts the owner when an unknown face is detected — 
with photo evidence and location!

## ✨ Features
- ✅ Face Recognition using OpenCV
- 📧 Real-time Email Alert with intruder photo
- 📍 IP based location tracking
- 🔒 Auto screen lock after wrong attempts
- 📵 Offline mode — stores alerts locally
- 🔑 OTP based remote access approval
- 📷 Camera privacy reminder after login
- 🔄 Auto sync pending alerts when internet returns

## 🛠️ Tech Stack
- Python 3.13
- OpenCV 4.10
- Tkinter (UI)
- SMTP Gmail API
- ip-api.com (Location)

## ⚙️ How to Run

### Install requirements:
pip install opencv-contrib-python deepface requests

### Register your face:
py register_face.py

### Start FaceGuard:
py guard.py

## 📁 Project Structure
