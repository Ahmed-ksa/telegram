from flask import Flask, request
import pyrebase
import random
import string
import datetime
import requests
import os

app = Flask(__name__)

firebaseConfig = {
    "apiKey": os.environ.get("FIREBASE_API_KEY"),
    "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN"),
    "databaseURL": os.environ.get("FIREBASE_DB_URL"),
    "projectId": os.environ.get("FIREBASE_PROJECT_ID"),
    "storageBucket": os.environ.get("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.environ.get("FIREBASE_MSG_SENDER_ID"),
    "appId": os.environ.get("FIREBASE_APP_ID")
}

firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()

BOT_TOKEN = os.environ.get("BOT_TOKEN")

def generate_password(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def send_to_telegram(chat_id, username, password, expiry):
    message = f"""شكراً لاشتراكك في الخدمة 🎉
فيما يلي بيانات حسابك:

👤 اسم المستخدم: `{username}`
🔒 كلمة المرور: `{password}`
📅 تاريخ انتهاء الاشتراك: `{expiry}`

⚠️ يُمنع مشاركة الحساب مع الآخرين."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    requests.post(url, data=data)

@app.route("/tap_webhook", methods=["POST"])
def tap_webhook():
    data = request.json
    if data.get("status") == "CAPTURED":
        internal_id = data.get("metadata", {}).get("internal_id")
        if not internal_id:
            return "No internal_id", 400

        chat_id = str(internal_id).strip()
        username = chat_id
        user_data = db.child("users").child(username).get().val()

        if user_data and "password" in user_data:
            password = user_data["password"]
        else:
            password = generate_password()

        expiry = datetime.datetime.now() + datetime.timedelta(days=30)

        db.child("users").child(username).update({
            "password": password,
            "expiry": expiry.strftime("%Y-%m-%d")
        })

        send_to_telegram(chat_id, username, password, expiry.strftime("%Y-%m-%d"))
        print(f"✅ تم إرسال الحساب إلى {chat_id}")

    return "OK", 200

if __name__ == "__main__":
    app.run(port=5000)