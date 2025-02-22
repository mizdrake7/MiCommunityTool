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

import requests, json, hashlib, urllib.parse, time, sys, os, base64, ntplib
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse, quote

version = "dev"

print(f"\n[V{version}] For issues or feedback:\n- GitHub: github.com/offici5l/MiCommunityTool/issues\n- Telegram: t.me/Offici5l_Group\n")

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
    with open('micdata.json') as f: micdata = json.load(f)
    print(f"\nAccount ID: {micdata['userId']}")
    input("Press 'Enter' to continue.\nPress 'Ctrl' + 'd' to log out.")
except (FileNotFoundError, json.JSONDecodeError, EOFError):
    if os.path.exists('micdata.json'):
        os.remove('micdata.json')
    micdata = login()

serviceToken = micdata["serviceToken"]
api = "https://sgp-api.buy.mi.com/bbs/api/global/"
U_state = api + "user/bl-switch/state"
U_apply = api + "apply/bl-auth"

def state_request():
    print("\n[STATE]:")
    try:
        state = requests.get(U_state, headers=headers, cookies=serviceToken).json().get("data", {})
        is_ = state.get("is_pass")
        button_ = state.get("button_state")
        deadline_ = state.get("deadline_format", "")
        if is_ == 1:
            exit(f"You have been granted access to unlock until Beijing time {deadline_} (mm/dd/yyyy)\n")
        msg = {
            1: "Apply for unlocking\n",
            2: f"Account Error Please try again after {deadline_} (mm/dd)\n",
            3: "Account must be registered over 30 days\n"
        }
        print(msg.get(button_, ""))
        if button_ in [2, 3]:
            exit()
    except Exception as e:
        exit(f"state: {e}")

state_request()

def apply_request():
    print("\n[APPLY]:")
    try:
        apply = requests.post(U_apply, data='{"is_retry":true}', headers=headers, cookies=serviceToken)
        print(f"Server response time: {apply.headers['Date']}")
        if apply.json().get("code") != 0:
            exit(apply.json())
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
            state_request()
        elif apply_ in [4, 5, 6, 7]:
            exit()
        elif apply_ == 3:
            return 1
    except Exception as e:
        exit(f"apply: {e}")


def get_ntp_time(servers=["cn.pool.ntp.org", "time.apple.com", "pool.ntp.org"]):
    client = ntplib.NTPClient()
    for server in servers:
        try:
            response = client.request(server, version=3, timeout=1)
            return datetime.fromtimestamp(response.tx_time, timezone.utc)
        except Exception:
            continue
    return datetime.now(timezone.utc)

def get_beijing_time():
    return get_ntp_time().astimezone(timezone(timedelta(hours=8)))

def precise_sleep(target_time):
    while (diff := (target_time - get_beijing_time()).total_seconds()) > 0:
        time.sleep(max(diff * 0.5, 0.001))

def measure_latency(url, samples=3, method='HEAD'):
    latencies = []
    for _ in range(samples):
        try:
            start = time.perf_counter()
            (requests.head if method == 'HEAD' else requests.post)(url, timeout=1)
            latencies.append((time.perf_counter() - start) * 1000)
        except:
            pass
    return min((sum(sorted(latencies)[:3])/3)*1.5, 2500) if latencies else 2000

def schedule_daily_task():
    SAFETY_THRESHOLD = 500 
    MAX_ALLOWED_LATENCY = 1500 

    while True:
        now = get_beijing_time()
        midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        start_calc_time = midnight - timedelta(minutes=5)
        
        if now < start_calc_time:
            print(f"\n[INFO] Calculations will begin at: {start_calc_time.strftime('%H:%M:%S')} CST")
            precise_sleep(start_calc_time)
        
        print("\n[INFO] Starting initial measurements...")
        base_latency = measure_latency(U_apply, samples=5, method='POST')
        print(f"Initial latency: {base_latency:.0f}ms")
        
        dynamic_time = midnight - timedelta(seconds=60)
        precise_sleep(dynamic_time)
        print("\n[INFO] Starting dynamic measurements...")
        dynamic_latency = measure_latency(U_apply, samples=3, method='HEAD')
        print(f"Dynamic latency: {dynamic_latency:.0f}ms")
        
        final_target = midnight - timedelta(milliseconds=SAFETY_THRESHOLD)
        precise_sleep(final_target)
        print("\n[INFO] Starting final measurements...")
        final_latency = measure_latency(U_apply, samples=2, method='HEAD')
        print(f"Final latency: {final_latency:.0f}ms")
        
        adjusted_latency = min((base_latency * 0.2) + (dynamic_latency * 0.3) + (final_latency * 0.5), MAX_ALLOWED_LATENCY)
        execution_time = midnight - timedelta(milliseconds=adjusted_latency)
        
        if execution_time < (midnight - timedelta(milliseconds=SAFETY_THRESHOLD)):
            execution_time = midnight - timedelta(milliseconds=SAFETY_THRESHOLD)
        
        print(f"\n[INFO] Final execution time: {execution_time.strftime('%H:%M:%S.%f')[:-3]} | Latency: {adjusted_latency:.0f}ms")
        precise_sleep(execution_time)
        
        if get_beijing_time() < midnight + timedelta(seconds=1):
            result = apply_request()
            if result == 1:
                return 1
        else:
            print("\nMissed the sending window! Retrying tomorrow.")



while True:
    result = schedule_daily_task()
    if result != 1:
        break


