import requests, json, hashlib, urllib.parse, time, shelve, sys, binascii, hmac, re  
from datetime import datetime, timedelta, timezone

version = "1.1"

print(f"\n[V{version}] For issues or feedback:\n- GitHub: github.com/offici5l/MiCommunityTool/issues\n- Telegram: t.me/Offici5l_Group\n")

headers = {"User-Agent": "offici5l/MiCommunityTool"}

user = input('\nEnter user: ')
pwd = input('\nEnter pwd: ')

try:
    r1 = requests.post("https://account.xiaomi.com/pass/serviceLoginAuth2", headers=headers, data={"callback": "https://sgp-api.buy.mi.com/bbs/api/global/user/login-back?followup=https%3A%2F%2Fnew.c.mi.com%2Fglobal%2F&sign=NTRhYmNhZWI1ZWM2YTFmY2U3YzU1NzZhOTBhYjJmZWI1ZjY3MWNiNQ%2C%2C", "sid": "18n_bbs_global", "_sign": "Phs2y/c0Xf7vJZG9Z6n9c+Nbn7g=", "user": user, "hash": hashlib.md5(pwd.encode(encoding='utf-8')).hexdigest().upper(), "_json": "true"})
    json_data = json.loads(r1.text[11:])
    if json_data["code"] == 70016: exit("invalid user or pwd")
    location_url = json_data['location']
    r2 = requests.get(location_url, headers=headers, allow_redirects=False)
    cookies = r2.cookies.get_dict()
except Exception as e:
    exit(e)

    
api = "https://sgp-api.buy.mi.com/bbs/api/global/"

url_state = api + "user/bl-switch/state"
url_apply = api + "apply/bl-auth"


def state_request():
    print("\n[STATE]:")
    state = requests.get(url_state, headers=headers, cookies=cookies).json()
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
    apply = requests.post(url_apply, headers=headers, data=data, cookies=cookies).json()
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
            exit()
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

beijing_tz = timezone(timedelta(hours=8))
now = datetime.now(beijing_tz)

target_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
if now >= target_time:
    target_time += timedelta(days=1)

def measure_latency():
    total_rtt = 0
    successful = 0
    for _ in range(3):
        try:
            start = time.perf_counter()
            response = requests.head(url_apply, headers=headers, timeout=2)
            response.raise_for_status()
            total_rtt += (time.perf_counter() - start) * 1000
            successful += 1
        except:
            continue
    return total_rtt / successful if successful > 0 else 100 

latency = measure_latency()
safety_margin = 50
adjusted_time = target_time - timedelta(milliseconds=latency + safety_margin)

while datetime.now(beijing_tz) < adjusted_time:
    print(f"""\r{datetime.now(beijing_tz).strftime("%H:%M:%S.%f%z")} => {adjusted_time.strftime("%H:%M:%S.%f%z")}      """, end="", flush=True)

apply_request()