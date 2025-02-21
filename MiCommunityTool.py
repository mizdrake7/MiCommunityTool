#!/usr/bin/python

import os
import importlib

while True:
    for lib in ['requests', 'ntplib']:
        try:
            importlib.import_module(lib)
        except ModuleNotFoundError:
            os.system(f'pip install {lib}')
            break
    else:
        break

import requests, json, hashlib, urllib.parse, time, sys, threading
from datetime import datetime, timedelta, timezone
import ntplib

version = "1.1"

print(f"\n[V{version}] For issues or feedback:\n- GitHub: github.com/offici5l/MiCommunityTool/issues\n- Telegram: t.me/Offici5l_Group\n")

headers = {"User-Agent": "offici5l/MiCommunityTool"}

user = input('\nEnter user: ')
pwd = input('\nEnter pwd: ')

try:
    r1 = requests.post("https://account.xiaomi.com/pass/serviceLoginAuth2", headers=headers, data={"callback": "https://sgp-api.buy.mi.com/bbs/api/global/user/login-back?followup=https%3A%2F%2Fnew.c.mi.com%2Fglobal%2F&sign=NTRhYmNhZWI1ZWM2YTFmY2U3YzU1NzZhOTBhYjJmZWI1ZjY3MWNiNQ%2C%2C", "sid": "18n_bbs_global", "_sign": "Phs2y/c0Xf7vJZG9Z6n9c+Nbn7g=", "user": user, "hash": hashlib.md5(pwd.encode('utf-8')).hexdigest().upper(), "_json": "true", "serviceParam": '{"checkSafePhone":false,"checkSafeAddress":false,"lsrp_score":0.0}'})
    json_data = json.loads(r1.text[11:])
    if json_data["code"] == 70016: exit("invalid user or pwd")
    if "notificationUrl" in json_data:
        check = json_data["notificationUrl"]
        if "SetEmail" in check:
            exit(f"Verification, please add an email to the account: {check}")
        elif "BindAppealOrSafePhone" in check:
            exit(f"Verification, please add an phone number to the account: {check}")
        else:
            exit(f"check: {check}")
    region = json.loads(requests.get(f"https://account.xiaomi.com/pass/user/login/region", headers=headers, cookies=r1.cookies.get_dict()).text[11:])["data"]["region"]
    print(f"\nAccount Region: {region}")
    location_url = json_data['location']
    r2 = requests.get(location_url, headers=headers, allow_redirects=False)
    cookies = r2.cookies.get_dict()
except Exception as e:
    exit(f"Error: {e}")


api = "https://sgp-api.buy.mi.com/bbs/api/global/"

url_state = api + "user/bl-switch/state"
url_apply = api + "apply/bl-auth"

# url_info = api + "user/data"
# info = requests.get(url_info, headers=headers, cookies=cookies).json()
#print(info)

def state_request():
    print("\n[STATE]:")
    try:
        state = requests.get(url_state, headers=headers, cookies=cookies).json()
    except Exception as e:
        exit(f"state: {e}")
    if 'data' in state:
        state_data = state.get("data")
        is_pass = state_data.get("is_pass")
        button_state = state_data.get("button_state")
        deadline_format = state_data.get("deadline_format", "")
        if is_pass == 1:
            print(f"You have been granted access to unlock until Beijing time {deadline_format} (mm/dd/yyyy)\n")
            exit()
        else:
            if button_state == 1:
                print("Apply for unlocking\n")
            elif button_state == 2:
                print(f"Account Error Please try again after {deadline_format} (mm/dd)\n")
                exit()
            elif button_state == 3:
                print("Account must be registered over 30 days\n")
                exit()


def apply_request():
    # is_retry: true/false ?!
    data = '{"is_retry":true}'
    try:
        apply = requests.post(url_apply, headers=headers, data=data, cookies=cookies).json()
    except Exception as e:
        exit(f"apply: {e}")  
    data = apply["data"]
    code = apply["code"]
    if code == 0:
        apply_result = data.get("apply_result")
        if apply_result == 1:
            print("Application Successful")
            state_request()
            exit()
        elif apply_result == 4:
            deadline_format = data.get("deadline_format")
            date, time = deadline_format.split()
            print(f"\nAccount Error Please try again after {deadline_format} (mm/dd)\n")
            exit()
        elif apply_result == 3:
            deadline_format = data.get("deadline_format")
            date, time = deadline_format.split()
            print(f"\nApplication quota limit reached, please try again after {date} (mm/dd) {time} (GMT+8)\n")
            return 1
        elif apply_result == 5:
            print("\nApplication failed. Please try again later\n")
            exit()
        elif apply_result == 6:
            print("\nPlease try again in a minute\n")
            exit()
        elif apply_result == 7:
            print("\nPlease try again later\n")
            exit()
    elif code == 100003:
        print("\nFail\n")
        exit()
    elif code == 100001:
        print("\nInvalid parameters\n")
        exit()

state_request()

def china_time():
    print("\nPress Enter to send the request\n")
    stop = False
    def check_input():
        nonlocal stop
        input()
        stop = True
    threading.Thread(target=check_input, daemon=True).start()
    while not stop:
        china_time = datetime.now(timezone(timedelta(hours=8)))
        local_time = datetime.now().astimezone()
        sys.stdout.write(f"\rTime: [China: {china_time.strftime('%H:%M:%S.%f')[:-3]}]  |  [Local: {local_time.strftime('%H:%M:%S.%f')[:-3]}]")
        sys.stdout.flush()

china_time()

if apply_request() == 1:
    while True:
        try:
            input("\nPress Enter to try again\n(Ctrl+d to exit)\n")
            apply_request()
        except (EOFError):
            exit()