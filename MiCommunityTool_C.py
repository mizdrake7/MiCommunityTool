#!/usr/bin/python

import os
import importlib

while True:
    for lib in ['requests']:
        try:
            importlib.import_module(lib)
        except ModuleNotFoundError:
            os.system(f'pip install {lib}')
            break
    else:
        break

import requests, json, hashlib, urllib.parse, time, sys, os, base64, argparse, re
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse, quote

version = "1.5(C)"
print(f"\n[V{version}] For issues or feedback:\n- GitHub: github.com/offici5l/MiCommunityTool/issues\n- Telegram: t.me/Offici5l_Group\n")

parser = argparse.ArgumentParser(description="set a specific execution time(china time).")
parser.add_argument(
    "--time",
    type=str,
    default="00:00:00:000000",
    help="Specify the target execution time in the format: HH:MM:SS:UUUUUU (e.g., 23:59:59:000000)"
)
args = parser.parse_args()

match = re.match(r"(\d+):(\d+):(\d+):(\d+)", args.time)
if match:
    target_hour, target_minute, target_second, target_microsecond = map(int, match.groups())
else:
    raise ValueError("Invalid time format. Use: HH:MM:SS:UUUUUU")

print(f"Selected time: {target_hour:02}:{target_minute:02}:{target_second:02}:{target_microsecond:06}")


User = "offici5l/MiCommunityTool"
headers = {"User-Agent": User}

def login():
    base_url = "https://account.xiaomi.com"
    sid = "18n_bbs_global"

    user = input('\nEnter user: ')
    pwd = input('\nEnter pwd: ')
    hash_pwd = hashlib.md5(pwd.encode()).hexdigest().upper()
    cookies = {}

    def parse(res): return json.loads(res.text[11:])

    r = requests.get(f"{base_url}/pass/serviceLogin", params={'sid': sid, '_json': True}, headers=headers, cookies=cookies)
    cookies.update(r.cookies.get_dict())
    data = {k: v[0] for k, v in parse_qs(urlparse(parse(r)['location']).query).items()}
    data.update({'user': user, 'hash': hash_pwd})

    r = requests.post(f"{base_url}/pass/serviceLoginAuth2", data=data, headers=headers, cookies=cookies)
    cookies.update(r.cookies.get_dict())
    res = parse(r)

    if res["code"] == 70016: exit("invalid user or pwd")
    if 'notificationUrl' in res:
        url = res['notificationUrl']
        if any(x in url for x in ['callback','SetEmail','BindAppealOrSafePhone']): exit(url)

        cookies.update({"NativeUserAgent": base64.b64encode(User.encode()).decode()})
        params = parse_qs(urlparse(url).query)
        cookies.update(requests.get(f"{base_url}/identity/list", params=params, headers=headers, cookies=cookies).cookies.get_dict())

        email = parse(requests.get(f"{base_url}/identity/auth/verifyEmail", params={'_json': True}, cookies=cookies, headers=headers))['maskedEmail']
        quota = parse(requests.post(f"{base_url}/identity/pass/sms/userQuota", data={'addressType': 'EM', 'contentType': 160040}, cookies=cookies, headers=headers))['info']
        print(f"Account Authentication\nemail: {email}, Remaining attempts: {quota}")
        input("\nPress Enter to send the verification code")

        code_res = parse(requests.post(f"{base_url}/identity/auth/sendEmailTicket", cookies=cookies, headers=headers))

        if code_res["code"] == 0: print(f"\nVerification code sent to your {email}")
        elif code_res["code"] == 70022: exit("Sent too many codes. Try again tomorrow.")
        else: exit(code_res)

        while True:
            ticket = input("Enter code: ").strip()
            v_res = parse(requests.post(f"{base_url}/identity/auth/verifyEmail", data={'ticket':ticket, 'trust':True}, cookies=cookies, headers=headers))
            if v_res["code"] == 70014: print("Verification code error")
            elif v_res["code"] == 0:
                cookies.update(requests.get(v_res['location'], headers=headers, cookies=cookies).history[1].cookies.get_dict())
                cookies.pop("pass_ua", None)
                break
            else: exit(v_res)

        r = requests.get(f"{base_url}/pass/serviceLogin", params={'_json': "true", 'sid': sid}, cookies=cookies, headers=headers)
        res = parse(r)

    nonce, ssecurity = res['nonce'], res['ssecurity']
    res['location'] += f"&clientSign={quote(base64.b64encode(hashlib.sha1(f'nonce={nonce}&{ssecurity}'.encode()).digest()))}"
    serviceToken = requests.get(res['location'], headers=headers, cookies=cookies).cookies.get_dict()

    micdata = {"userId": res['userId'], "serviceToken": serviceToken}
    with open("micdata.json", "w") as f: json.dump(micdata, f)
    return micdata

try:
    with open('micdata.json') as f:
        micdata = json.load(f)
    if not all(micdata.get(k) for k in ("userId", "serviceToken")):
        raise ValueError
    print(f"\nAccount ID: {micdata['userId']}")
    input("Press 'Enter' to continue.\nPress 'Ctrl' + 'd' to log out.")
except (FileNotFoundError, json.JSONDecodeError, EOFError, ValueError):
    if os.path.exists('micdata.json'):
        os.remove('micdata.json')
    micdata = login()

serviceToken = micdata["serviceToken"]

def apply_request():
    print("\n[APPLY]:")
    try:
        apply = requests.post("https://sgp-api.buy.mi.com/bbs/api/global/apply/bl-auth", data='{"is_retry":true}', headers=headers, cookies=serviceToken)
        print(f"Server response time: {apply.headers['Date']}")
        if apply.json().get("code") != 0:
            print(apply.json())
            return
        data_ = apply.json().get("data", {}) or {}
        apply_ = data_.get("apply_result", 0)
        deadline_ = data_.get("deadline_format", "")
        messages = {
            1: "Application Successful",
            4: f"\nAccount Error Please try again after {deadline_} (mm/dd)\n",
            3: f"\nApplication quota limit reached, please try again after {deadline_.split()[0]} (mm/dd) {deadline_.split()[1]} (GMT+8)\n",
            5: "\nApplication failed. Please try again later\n",
            6: "\nPlease try again in a minute\n",
            7: "\nPlease try again later\n"
        }
        print(messages.get(apply_, ""))
        if apply_ == 1:
            exit()
        else:
            return
    except Exception as e:
        print(e)
        return

def schedule_daily_task():
    beijing_tz = timezone(timedelta(hours=8))
    while True:
        now = datetime.now(beijing_tz)
        target = now.replace(
            hour=target_hour,
            minute=target_minute,
            second=target_second,
            microsecond=target_microsecond
        )
        if now >= target:
            target += timedelta(days=1)
        print(f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S.%f')}", flush=True)
        print(f"Target time: {target.strftime('%Y-%m-%d %H:%M:%S.%f')}", flush=True)
        sleep_time = (target - now).total_seconds()
        print(f"Sleeping for {sleep_time:.2f} seconds ({sleep_time / 60:.2f} minutes) until execution...", flush=True)
        time.sleep(sleep_time)
        print("Executing apply_request() now...", flush=True)
        apply_request()
        return


while True:
    schedule_daily_task()