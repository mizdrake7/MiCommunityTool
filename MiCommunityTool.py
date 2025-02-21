#!/usr/bin/python

version = "1.0"

exit("Warning: The tool is currently unstable. Please do not use it until a new update is released soon.")

print(f"\n[V{version}] For issues or feedback:\n- GitHub: github.com/offici5l/MiCommunityTool/issues\n- Telegram: t.me/Offici5l_Group\n")



import os
import importlib

for lib in ['requests', 'urllib3']:
    try:
        importlib.import_module(lib)
    except ModuleNotFoundError:
        os.system(f'pip install {lib}')

import requests, json, hashlib, urllib.parse, sys, threading
from datetime import datetime, timezone, timedelta
from base64 import b64encode, b64decode

# for global
sid = "18n_bbs_global"
api = "https://sgp-api.buy.mi.com/bbs/api/global/"

# for info: api + "user/data"
url_state = api + "user/bl-switch/state"
url_apply = api + "apply/bl-auth"

# version com.mi.global.bbs 
version_name = "5.4.11"
version_code = "500411"

base = "https://account.xiaomi.com/"
auth1 = base + "pass/serviceLogin"
auth2 = base + "pass/serviceLoginAuth2"

def login():
    try:
        user = input('Enter user: ')
        hash = hashlib.md5(input('Enter pwd: ').encode()).hexdigest().upper()
        data = {'user': user, 'hash': hash}
        params = {"_json": "true"}
        r1 = requests.post(auth2, data=data, params=params)
        r1_text = json.loads(r1.text[11:])
        if "notificationUrl" in r1_text:
            check = r1_text["notificationUrl"]
            if "SetEmail" in check:
                exit("Add email to account")
            if "BindAppealOrSafePhone" in check:
                exit("Add phone number to account")
        if r1_text["code"] == 70016:
            exit("invalid user or pwd")
        cookies = r1.cookies.get_dict()
    except Exception as e:
        exit(f"r1: {type(e).__name__}")

    cookies = {k: cookies[k] for k in ['deviceId', 'passToken', 'userId']}
    with open("micookies.json", "w") as f:
        json.dump(cookies, f, indent=4)

    return cookies


try:
    with open('micookies.json', 'r') as f:
        cookies = json.load(f)
    input(f"userId: {cookies['userId']}, you are already logged in\nPress Enter to continue or Ctrl+d to log out.\n")
except (FileNotFoundError, json.JSONDecodeError, EOFError):
    if os.path.exists('micookies.json'):
        os.remove('micookies.json')
    cookies = login()


try:
    params = {"sid": sid, "_json": "true"}
    r2 = requests.get(auth1, cookies=cookies, params=params)
    r2_text = json.loads(r2.text[11:])
    location = r2_text["location"]
    nonce = r2_text["nonce"]
    ssecurity = r2_text["ssecurity"]
    sign = b64encode(hashlib.sha1(f'nonce={nonce}&{ssecurity}'.encode()).digest()).decode()
    clientSign = urllib.parse.quote_plus(sign)
    new_bbs_serviceToken = requests.get(f"{location}&clientSign={clientSign}").cookies.get_dict()["new_bbs_serviceToken"]
except (KeyError, requests.RequestException, json.JSONDecodeError) as e:
    exit(f"Error: {e}")

headers = {"Cookie": f"new_bbs_serviceToken={new_bbs_serviceToken}; versionCode={version_code}; versionName={version_name}; deviceId={cookies['deviceId']}"}

def state_request():
    print("\n[STATE]:")
    state = requests.get(url_state, headers=headers).json()
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
                return 0
            elif button_state == 2:
                print(f"Account Error Please try again after {deadline_format} (mm/dd)\n")
                exit()
            elif button_state == 3:
                print("Account must be registered over 30 days\n")
                exit()


def apply_request():
    # is_retry: true/false ?!
    data = '{"is_retry":true}'
    apply = requests.post(url_apply, headers=headers, data=data).json()
    data = apply["data"]
    code = apply["code"]
    if code == 0:
        apply_result = data.get("apply_result")
        deadline_format = data.get("deadline_format")
        date, time = deadline_format.split()
        if apply_result == 1:
            print("Application Successful")
            state_request()
            exit()
        elif apply_result == 4:
            print(f"\nAccount Error Please try again after {deadline_format} (mm/dd)\n")
            exit()
        elif apply_result == 3:
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

