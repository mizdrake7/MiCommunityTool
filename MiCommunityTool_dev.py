import requests, json, hashlib, urllib.parse, time, sys
from datetime import datetime, timedelta, timezone
import ntplib

version = "dev"

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

def get_ntp_time(servers=["pool.ntp.org", "time.google.com", "time.windows.com"]):
    client = ntplib.NTPClient()
    for server in servers:
        try:
            response = client.request(server, version=3, timeout=5)
            return datetime.fromtimestamp(response.tx_time, timezone.utc)
        except Exception:
            continue
    return datetime.now(timezone.utc)

def get_beijing_time():
    utc_time = get_ntp_time()
    return utc_time.astimezone(timezone(timedelta(hours=8)))

def precise_sleep(target_time, precision=0.01):
    while True:
        diff = (target_time - datetime.now(target_time.tzinfo)).total_seconds()
        if diff <= 0:
            return
        sleep_time = max(min(diff - precision/2, 1), precision)
        time.sleep(sleep_time)

def measure_latency(url, samples=5):
    latencies = []
    for _ in range(samples):
        try:
            start = time.perf_counter()
            requests.post(url, headers=headers, data='{}', timeout=2)
            latencies.append((time.perf_counter() - start) * 1000)
        except Exception:
            continue
    
    if len(latencies) < 3:
        return 200
    
    latencies.sort()
    trim = int(len(latencies) * 0.2)
    trimmed = latencies[trim:-trim] if trim else latencies
    return sum(trimmed)/len(trimmed) * 1.3

def schedule_daily_task():
    beijing_tz = timezone(timedelta(hours=8))
    
    while True:
        now = get_beijing_time()
        target = now.replace(hour=23, minute=57, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        
        print(f"\nNext execution at: {target.strftime('%Y-%m-%d %H:%M:%S.%f')} CST")
        while datetime.now(beijing_tz) < target:
            time_left = (target - datetime.now(beijing_tz)).total_seconds()
            if time_left > 300:
                time.sleep(60)
            else:
                precise_sleep(target)
        
        latency = measure_latency(url_apply)
        execution_time = target + timedelta(minutes=3) - timedelta(milliseconds=latency)
        
        print(f"Adjusted execution time: {execution_time.strftime('%H:%M:%S.%f')}")
        precise_sleep(execution_time)
        
        result = apply_request()
        if result == 1:
            return 1


while True:
    result = schedule_daily_task()
    if result != 1:
        break