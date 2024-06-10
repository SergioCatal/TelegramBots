import time
import requests
import json
import pprint


def non_blocking(handler):
    def wrapper(*args, **kwargs):
        try:
            return handler(*args, **kwargs)
        except Exception as e:
            print(f"ERROR <Unable to send GET request>: {e}")
            return None

    return wrapper


@non_blocking
def req_get(*args, **kwargs):
    return requests.get(*args, **kwargs)


class TelegramBot:
    def __init__(self, token, commands):
        base_url = f"https://api.telegram.org/bot{token}"
        self.send_message_url = f"{base_url}/sendMessage"
        self.get_updates_url = f"{base_url}/getUpdates"
        self.set_commands_url = f"{base_url}/setMyCommands"

        self.last_update_id = None
        self.set_commands(commands)

    def send_message(self, chat_id, text):
        res = req_get(f"{self.send_message_url}?chat_id={chat_id}&text={text}")
        return res.status_code if res else None

    def receive_messages(self):
        if self.last_update_id is None:
            res = req_get(f"{self.get_updates_url}")
        else:
            res = req_get(f"{self.get_updates_url}?offset={self.last_update_id + 1}")

        if res is None:
            return None

        res_dict = res.json()
        pprint.pprint(res_dict)
        if not res_dict["ok"]:
            print("ERROR: Updates from telegram are NOT OK!")
            return None

        updates = res_dict["result"]
        if len(updates) > 0:
            self.last_update_id = updates[-1]["update_id"]
        return updates

    def set_commands(self, commands):
        res = req_get(f"{self.set_commands_url}?commands={json.dumps(commands)}")
        if not res or res.status_code != 200:
            print(f"ERROR: Unable to set bot commands!\n{res.text}")


if __name__ == "__main__":
    test_commands = [{"command": "status", "description": "Show status of subscribed symbols"},
                     {"command": "add_symbol", "description": "Show status of subscribed symbols"}]
    b = TelegramBot(test_commands)
    while True:
        print(b.receive_messages())
        time.sleep(5)

# [{'update_id': 951230211, 'message': {'message_id': 27, 'from': {'id': 128341958, 'is_bot': False, 'first_name': 'Sergio', 'username': 'sergio_1689', 'language_code': 'en'}, 'chat': {'id': 128341958, 'first_name': 'Sergio', 'username': 'sergio_1689', 'type': 'private'}, 'date': 1704149623, 'text': '/status', 'entities': [{'offset': 0, 'length': 7, 'type': 'bot_command'}]}}]
