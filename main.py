import time
import requests
import pprint
import datetime
from yaml import load, dump, YAMLError
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

# TODO: TO IMPLEMENT
# TODO: - Allow users to message back to the bot to notify a completed cleaning task
# TODO: - Make a conda environment for this
# TODO: - Add proper error handling


def read_yaml_file_and_check_for_items(file_path, required_items):
    try:
        with open(file_path, "r") as f:
            yaml_contents = load(f, Loader)
            yaml_keys = yaml_contents.keys()
            for req_item in required_items:
                if req_item not in yaml_keys:
                    print(f"ERROR: Yaml file {file_path} does not contain item {req_item}")
                    exit(1)
            return yaml_contents
    except OSError as e:
        print(f"ERROR: Unable to open yaml configuration file!\n{e}")
        exit(1)
    except YAMLError as e:
        print(f"ERROR: Unable to parse yaml configuration file!\n{e}")
        exit(1)


def get_telegram_configs():
    configs = read_yaml_file_and_check_for_items("secrets.yaml", ["token", "group_id"])
    return configs["token"], configs["group_id"]


# Telegram stuff
API_TOKEN, GROUP_ID = get_telegram_configs()
BASE_URL = f"https://api.telegram.org/bot{API_TOKEN}"
SEND_MESSAGE_URL = f"{BASE_URL}/sendMessage"
GET_UPDATES_URL = f"{BASE_URL}/getUpdates"


def get_updates():
    res = requests.get(f"{GET_UPDATES_URL}")
    pprint.pprint(res.json())


def send_message(user, text):
    res = requests.get(f"{SEND_MESSAGE_URL}?chat_id={user}&text={text}")
    return res.status_code


def get_week_number():
    # Compute the weeknumber from today (the -1 is so that a week starts from monday and not sunday)
    return (datetime.date.today().toordinal() - 1) // 7


class CleaningSchedules:
    def __init__(self, config_file_path):
        configs = read_yaml_file_and_check_for_items(config_file_path, ["users", "tasks"])
        self.job_list = configs["tasks"]
        self.users_list = configs["users"]

    def build_jobs_msg(self):
        assigned_task = self._assign_tasks()
        msg = "Cleaning Tasks for this weekend:\n"
        for p, j in assigned_task.items():
            msg += f"- {p}: {self.job_list[j]}\n"
        return msg

    def _assign_tasks(self):
        week_number = get_week_number()
        task = week_number % len(self.users_list)
        assigned_task = {}
        for p in self.users_list:
            assigned_task[p] = task
            task = (task + 1) % len(self.users_list)
        return assigned_task


def get_wakeup_datetime():
    wake_up_day = datetime.date.today().toordinal() + 1
    wake_up_time = datetime.timedelta(hours=8)
    return datetime.datetime.fromordinal(wake_up_day) + wake_up_time


if __name__ == '__main__':
    cleaning_schedules = CleaningSchedules("configs.yaml")
    text = f"I'm alive bitches. This bot is set up for users {cleaning_schedules.users_list} with tasks {cleaning_schedules.job_list}"
    send_message(GROUP_ID, text)
    while True:
        # Handle cleaning schedules
        today = datetime.date.today().isoweekday()
        print(f"Processing day {today}!")
        if today == 6:
            # SATURDAY
            send_message(GROUP_ID, cleaning_schedules.build_jobs_msg())
        elif today == 7:
            # SUNDAY
            text = f"REMINDER!\n{cleaning_schedules.build_jobs_msg()}"
            send_message(GROUP_ID, text)

        wakeup_datetime = get_wakeup_datetime()
        time.sleep((wakeup_datetime - datetime.datetime.now()).total_seconds())
