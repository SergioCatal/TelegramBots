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
# TODO: - Load api token from file
# TODO: - Load settings from file
# TODO: - Have a fixed system to choose the cleaning shifts
# TODO: - Allow users to message back to the bot to notify a completed cleaning task
# TODO: - Make a conda environment for this
# TODO: - Add proper error handling


def get_telegram_configs():
    try:
        with open("secrets.yaml", "r") as f:
            secrets = load(f, Loader)
            if "token" not in secrets.keys() or "group_id" not in secrets.keys():
                print("ERROR: Token or GroupId not in yaml configuration file!")
                exit(1)

            return secrets["token"], secrets["group_id"]
    except OSError as e:
        print(f"ERROR: Unable to open yaml configuration file!\n{e}")
        exit(1)
    except YAMLError as e:
        print(f"ERROR: Unable to parse yaml configuration file!\n{e}")
        exit(1)


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


class CleaningSchedules:
    def __init__(self):
        self.job_list = ["BathroomBig", "BathroomSmall", "Kitchen", "LivingRoom"]
        self.assigned_job = {"Gabor": 1, "Luca": 3, "Rob": 2, "Sergio": 0}

    def build_jobs_msg(self):
        msg = "Cleaning Tasks for this weekend:\n"
        for p, j in self.assigned_job.items():
            msg += f"- {p}: {self.job_list[j]}\n"
        return msg

    def update_jobs(self):
        for p in self.assigned_job.keys():
            self.assigned_job[p] = (self.assigned_job[p] + 1) % 4


def get_wakeup_datetime():
    wake_up_day = datetime.date.today().toordinal() + 1
    wake_up_time = datetime.timedelta(hours=8)
    return datetime.datetime.fromordinal(wake_up_day) + wake_up_time


if __name__ == '__main__':
    last_update_day = None
    cleaning_schedules = CleaningSchedules()
    text = f"I'm alive bitches. Have a preview of this weekend!\n{cleaning_schedules.build_jobs_msg()}"
    send_message(GROUP_ID, text)
    while True:
        # Handle cleaning schedules
        today = datetime.date.today().isoweekday()
        if today != last_update_day:
            last_update_day = today
            print(f"Processing day {today}!")
            if today == 6:
                # SATURDAY
                send_message(GROUP_ID, cleaning_schedules.build_jobs_msg())
            elif today == 7:
                # SUNDAY
                text = f"REMINDER!\n{cleaning_schedules.build_jobs_msg()}"
                send_message(GROUP_ID, text)
                cleaning_schedules.update_jobs()

        wakeup_datetime = get_wakeup_datetime()
        time.sleep((wakeup_datetime - datetime.datetime.now()).total_seconds())
