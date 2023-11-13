import time
import requests
import json
import datetime
from enum import Enum
from argparse import ArgumentParser
from lxml import html
from yaml import load, dump, YAMLError
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

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


START_DATE_STR = "01122023"
END_DATE_STR = "31032024"
BASE_URL = f"https://tila.ayy.fi/calendar/?fd={START_DATE_STR}&ld={END_DATE_STR}&r=9,18,32"
LIVINGROOM_TABLE_XPATH = "//td[@id='olohuone']"
RANTSU_TABLE_XPATH = "//td[@id='rantsu']"
VAASIS_TABLE_XPATH = "//td[@id='Vaasis']"
print(BASE_URL)

# Telegram stuff
API_TOKEN, CHAT_ID = get_telegram_configs()
MESSAGE_URL = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage?chat_id={CHAT_ID}&text="


class SlotStatus(Enum):
    FREE = 0
    RESERVED = 1
    LOCKED = 2

def read_json(path):
    try:
        with open(path, "r") as f:
            json_data = json.load(f)
        return json_data
    except:
        return {}


def readable_date(day):
    return day.strftime("%a %b %d %Y")


def update(save_file):
    start_date = datetime.datetime.strptime(START_DATE_STR, "%d%m%Y").date()

    # Get HTML page
    res = requests.get(BASE_URL)
    if res.status_code != 200:
        print("ERROR")
        return

    # Parse html and retrieve table
    tree = html.fromstring(res.text)
    livingroom_table = tree.xpath(LIVINGROOM_TABLE_XPATH)[0].getparent()
    rantsu_table = tree.xpath(RANTSU_TABLE_XPATH)[0].getparent()
    vaasis_table = tree.xpath(VAASIS_TABLE_XPATH)[0].getparent()

    tables = [(livingroom_table, "Living Room"), (rantsu_table, "Rantasauna"), (vaasis_table, "Vaasankatu")]

    any_new_date = False

    # Go through table and find free days
    to_save = {"timestamp": datetime.datetime.now().ctime()}
    for table, name in tables:
        current_date = start_date
        free_dates = []
        for el in table.getchildren():
            if el.tag == "td":
                if "id" in el.attrib:
                    continue

                if "class" in el.attrib and el.attrib["class"] == "c_0":
                    free_dates.append(current_date)
                current_date += datetime.timedelta(days=1)

        # Go through free days and find weekends (i.e. Friday or Saturday)
        free_weekends = []
        for free_date in free_dates:
            weekday = free_date.weekday()
            if weekday == 4 or weekday == 5:
                free_weekends.append(free_date.toordinal())

        # Go through free days and find special days (e.g. Day before holiday)
        special_days = [(5,12)]
        free_special_days = []
        for free_date in free_dates:
            for special_day in special_days:
                if free_date.day == special_day[0] and free_date.month == special_day[1]:
                    free_special_days.append(free_date.toordinal())

        free_weekends = sorted(free_weekends + free_special_days)
        to_save[name] = free_weekends

        # Load past free days and compare to current ones
        is_different = True
        old_data = read_json(save_file)
        if len(old_data) > 0 and name in old_data:
            old_dates = old_data[name]

            if len(old_dates) == len(free_weekends) and all([free_weekends[i] == old_dates[i] for i in range(len(free_weekends))]):
                is_different = False

        if is_different:
            print(
                f'UPDATED SAUNA {name} FROM {old_data["timestamp"] if len(old_data) > 0 else "NoStoredData"} TO {to_save["timestamp"]}')
            any_new_date = True
        else:
            print(f"NOTHING NEW FOR SAUNA {name}")

    # Store new updated data
    with open(save_file, "w") as f:
        json.dump(to_save, f)

    return any_new_date, to_save


def send_free_days(free_days):
    message = "Heeelllooo, new shifts available during weekend in AYY saunas!\n\n"
    for key, item in free_days.items():
        if key == "timestamp":
            continue

        message += key + ":\n"
        for day in item:
            message += " - " + readable_date(datetime.date.fromordinal(day)) + "\n"
    message_response = requests.get(MESSAGE_URL + message)
    print(message_response.status_code)


def update_and_send_free_days(latest_update_file):
    updated, free_weekends = update(latest_update_file)
    if updated:
        send_free_days(free_weekends)


def send_alive_message():
    message_response = requests.get(MESSAGE_URL + "I'm still alive and working")
    print(message_response.status_code)


def show(last_update_path):
    last_data = read_json(last_update_path)
    if len(last_data) == 0:
        print("Unable to read last downloaded data file!")
        return

    print(f'Showing information downloaded on {last_data["timestamp"]}\n')
    for key, item in last_data.items():
        if key != "timestamp":
            last_data[key] = [datetime.date.fromordinal(int(d)) for d in item]
            print(f'{key}:')
            for day in last_data[key]:
                print("\t" + readable_date(day))
    print("\n")


class ExecutionType(Enum):
    update = "update"
    show = "show"

    def __str__(self):
        return self.name

    @staticmethod
    def getHelpStr():
        return "use 'update' to download new shifts from the ayy website, use 'show' to just show the last downloaded info"


if __name__ == '__main__':
    last_update_file_path = "last_update"

    ''' Use to get chat_id
    telegram_url = f"https://api.telegram.org/bot{API_TOKEN}/getUpdates"
    res = requests.get(telegram_url)
    print(res.text)
    exit(0)
    '''

    send_alive_message()
    update_and_send_free_days(last_update_file_path)
    time_interval_hrs = 4
    daily_frequency = 24 // time_interval_hrs
    alive_notification_days_interval = 10
    count_limit = alive_notification_days_interval * daily_frequency
    today = datetime.datetime.today()
    start_hour = (today.hour // time_interval_hrs) * time_interval_hrs
    next_update_time = datetime.datetime(today.year, today.month, today.day, start_hour, 0, 0, 0, today.tzinfo)
    next_update_time += datetime.timedelta(hours=time_interval_hrs)

    count = 0
    while True:
        time_diff = next_update_time - datetime.datetime.now()
        print(f"Waiting for {time_diff.total_seconds()/3600}h to reach time {next_update_time.strftime('%d/%m/%Y %H:%M:%S')}")
        time.sleep(time_diff.total_seconds())
        print(f"Updating at time {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        update_and_send_free_days(last_update_file_path)

        count += 1
        if count == count_limit:
            count = 0
            print("Sending alive message\n")
            send_alive_message()
        next_update_time += datetime.timedelta(hours=time_interval_hrs)
