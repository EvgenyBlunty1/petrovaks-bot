import os
import json
import requests
from flask import Flask, request, jsonify
from typing import Dict, Optional, List

app = Flask(__name__)

class PetrovaksBot:
    def __init__(self):
        self.user_sessions = {}

    def call_api_method(self, method: str, params: Dict, auth: Dict) -> Optional[Dict]:
        url = f"{auth['client_endpoint']}{method}"

        # 🔐 Передаём либо access_token, либо весь auth-блок
        if "access_token" in auth:
            params["auth"] = auth["access_token"]
        else:
            params["auth"] = {
                "application_token": auth.get("application_token"),
                "domain": auth.get("domain"),
                "member_id": auth.get("member_id")
            }

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

    def send_message(self, dialog_id: str, message: str, auth: Dict, keyboard: Optional[List] = None) -> bool:
        params = {
            "DIALOG_ID": dialog_id,
            "MESSAGE": message
        }
        if keyboard:
            params["KEYBOARD"] = {
                "BUTTONS": keyboard,
                "ONE_TIME": False,
                "INLINE": False
            }
        return self.call_api_method("im.message.add", params, auth)

    def create_button(self, text: str, payload: Dict) -> Dict:
        return {
            "TEXT": text,
            "ACTION": "TEXT",
            "ACTION_VALUE": json.dumps(payload),
            "BG_COLOR": "#29619b",
            "TEXT_COLOR": "#fff",
            "DISPLAY": "LINE"
        }

    def handle_user_response(self, user_id: int, dialog_id: str, payload: Dict, auth: Dict):
        if payload.get("step") == "greeting":
            msg = "Давай обсудим твою адаптацию. Вот что тебя ждёт!"
            keyboard = [[self.create_button("Я слушаю!", {"step": "listen"})]]
            self.send_message(dialog_id, msg, auth, keyboard)

        elif payload.get("step") == "listen":
            msg = "На портале есть всё: документы, обучение, контакты."
            keyboard = [[self.create_button("Расскажи про Битрикс", {"step": "bitrix"})]]
            self.send_message(dialog_id, msg, auth, keyboard)

        elif payload.get("step") == "bitrix":
            self.send_message(dialog_id, "Битрикс — это наша основная система для коммуникаций и задач.", auth)

bot = PetrovaksBot()

@app.route('/bitrix-webhook', methods=['POST'])
def handle_webhook():
    event_data = request.form.to_dict()
    auth = {
        "access_token": event_data.get("auth[access_token]"),
        "application_token": event_data.get("auth[application_token]"),
        "domain": event_data.get("auth[domain]"),
        "client_endpoint": event_data.get("auth[client_endpoint]"),
        "server_endpoint": event_data.get("auth[server_endpoint]"),
        "member_id": event_data.get("auth[member_id]"),
    }

    with open("log.txt", "a", encoding="utf-8") as f:
        f.write("\n[INCOMING EVENT]\n")
        f.write(json.dumps(event_data, ensure_ascii=False, indent=2) + "\n")

    event_type = event_data.get("event", "NO_EVENT")

    if event_type == "ONIMBOTJOINCHAT":
        dialog_id = event_data.get("data[PARAMS][DIALOG_ID]")
        user_id = int(event_data.get("data[PARAMS][USER_ID]", 0))

        welcome_msg = (
            "Привет! Я чат-бот Петровакс 👋\n"
            "Нажми кнопку ниже, чтобы начать!"
        )
        keyboard = [[
            bot.create_button("Привет! Давай знакомиться", {"step": "greeting"})
        ]]
        bot.send_message(dialog_id, welcome_msg, auth, keyboard)

    elif event_type == "ONIMBOTMESSAGEADD":
        dialog_id = event_data.get("data[PARAMS][DIALOG_ID]")
        user_id = int(event_data.get("data[PARAMS][FROM_USER_ID]", 0))

        try:
            action_value = event_data["data[PARAMS][ATTACH][KEYBOARD][BUTTONS][0][ACTION_VALUE]"]
            payload = json.loads(action_value)
            bot.handle_user_response(user_id, dialog_id, payload, auth)
        except Exception:
            msg = event_data.get("data[PARAMS][MESSAGE]", "").lower()
            if "привет" in msg:
                bot.send_message(dialog_id, "Привет! Я бот Петровакс 🧠", auth)
            else:
                bot.send_message(dialog_id, "Пожалуйста, нажми на кнопку 👇", auth)

    return jsonify({"status": "ok"}), 200

@app.route('/log')
def view_log():
    try:
        with open("log.txt", "r", encoding="utf-8") as f:
            return "<pre>" + f.read() + "</pre>"
    except Exception as e:
        return f"Ошибка чтения логов: {e}"
