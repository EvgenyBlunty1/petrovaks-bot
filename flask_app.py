import os
from flask import Flask, request, jsonify
import requests
import json
from typing import Dict, List, Optional

app = Flask(__name__)

class PetrovaksBot:
    def __init__(self, webhook_url: str, bot_id: int):
        self.webhook_url = webhook_url
        self.bot_id = bot_id
        self.user_sessions = {}

    def call_api_method(self, method: str, params: Dict) -> Optional[Dict]:
        url = f"{self.webhook_url}{method}"
        try:
            response = requests.post(url, json=params)
            response.raise_for_status()
            result = response.json()

            with open("log.txt", "a", encoding="utf-8") as f:
                f.write(f"\n[API RESPONSE for {method}]\n")
                f.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")

            return result
        except requests.exceptions.RequestException as e:
            with open("log.txt", "a", encoding="utf-8") as f:
                f.write(f"\n[API ERROR on {method}]: {str(e)}\n")
            return None

    def send_message(self, dialog_id: str, message: str, keyboard: Optional[List] = None) -> bool:
        params = {
            "DIALOG_ID": dialog_id,
            "MESSAGE": message,
            "BOT_ID": self.bot_id
        }
        if keyboard:
            params["KEYBOARD"] = {
                "BUTTONS": keyboard,
                "ONE_TIME": False,
                "INLINE": False
            }
        return self.call_api_method("im.message.add", params)

    def create_button(self, text: str, payload: Dict) -> Dict:
        return {
            "TEXT": text,
            "ACTION": "TEXT",
            "ACTION_VALUE": json.dumps(payload),
            "BG_COLOR": "#29619b",
            "TEXT_COLOR": "#fff",
            "DISPLAY": "LINE"
        }

    def handle_new_user(self, dialog_id: str, user_id: int):
        welcome_msg = (
            "Hello its Petrovax"
            "testetstest"
        )
        keyboard = [[
            self.create_button("Привет! Давай знакомиться", {"step": "greeting"})
        ]]
        self.send_message(dialog_id, welcome_msg, keyboard)
        self.user_sessions[user_id] = {"dialog_id": dialog_id}

    def handle_user_response(self, user_id: int, payload: Dict):
        if user_id not in self.user_sessions:
            return

        dialog_id = self.user_sessions[user_id]["dialog_id"]

        if payload.get("step") == "greeting":
            msg = "Давай обсудим твою адаптацию. Вот что тебя ждёт!"
            keyboard = [[self.create_button("Я слушаю!", {"step": "listen"})]]
            self.send_message(dialog_id, msg, keyboard)

        elif payload.get("step") == "listen":
            msg = " dasdsa"
            keyboard = [[self.create_button("dqwdasdsad", {"step": "bitrix"})]]
            self.send_message(dialog_id, msg, keyboard)

        elif payload.get("step") == "bitrix":
            self.send_message(dialog_id, "djkdanjdasnjasdjdasjdjjnadj")

bot = PetrovaksBot(
    webhook_url="https://petrovax.bitrix24.ru/rest/67/a3gvavley270e4w9/",
    bot_id=3790
)

@app.route('/bitrix-webhook', methods=['POST'])
def handle_webhook():
    try:
        event_data = request.form.to_dict()
    except Exception as e:
        event_data = {}
        with open("log.txt", "a", encoding="utf-8") as f:
            f.write(f"[ERROR parsing request data]: {str(e)}\n")

    with open("log.txt", "a", encoding="utf-8") as f:
        f.write("\n[INCOMING EVENT]\n")
        f.write(json.dumps(event_data, ensure_ascii=False, indent=2) + "\n")

    event_type = event_data.get("event", "NO_EVENT")

    if event_type == "ONIMBOTJOINCHAT":
        dialog_id = event_data.get("data[PARAMS][DIALOG_ID]")
        user_id = int(event_data.get("data[PARAMS][USER_ID]", 0))
        bot.handle_new_user(dialog_id, user_id)

    elif event_type == "ONIMBOTMESSAGEADD":
    dialog_id = event_data.get("data[PARAMS][DIALOG_ID]")
    user_id = int(event_data.get("data[PARAMS][FROM_USER_ID]", 0))

    # Попытка извлечь нажатую кнопку
    try:
        action_value = event_data["data[PARAMS][ATTACH][KEYBOARD][BUTTONS][0][ACTION_VALUE]"]
        payload = json.loads(action_value)
        bot.handle_user_response(user_id, payload)
    except Exception as e:
        # Если не кнопка — обычный текст
        message = event_data.get("data[PARAMS][MESSAGE]", "").lower()
        if "привет" in message:
            bot.send_message(dialog_id, "Привет, я бот Петровакс! 👋")
        else:
            bot.send_message(dialog_id, "Пожалуйста, нажми на кнопку 👇")

    return jsonify({"status": "ok"}), 200

@app.route('/log')
def view_log():
    try:
        with open("log.txt", "r", encoding="utf-8") as f:
            return "<pre>" + f.read() + "</pre>"
    except Exception as e:
        return f"Ошибка чтения логов: {e}"
