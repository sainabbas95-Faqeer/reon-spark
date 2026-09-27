import pandas as pd, glob, os, requests, json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "last_alarm_state.json")
NTFY_TOPIC = "reon-spark-bahadur-95"

def load_last_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f: return set(json.load(f))
    return set()

def save_state(s): 
    with open(STATE_FILE, 'w') as f: json.dump(list(s), f)

def send_push(title, msg):
    requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", data=msg.encode('utf-8'), headers={"Title": title, "Priority": "high"})

# Latest Events file dhoondo
event_files = glob.glob(os.path.join(BASE_DIR, "Events Report*.csv")) + glob.glob(os.path.join(BASE_DIR, "events*.csv"))
if not event_files:
    print("No Events file found, skipping"); exit(0)

latest = max(event_files, key=os.path.getctime)
df_events = pd.read_csv(latest, low_memory=False)
df_sites = pd.read_csv(os.path.join(BASE_DIR, "Sites List.csv"), low_memory=False)

df_events['site_name_clean'] = df_events['site_name'].astype(str).str.strip().str.upper()
df_sites['Site Id_clean'] = df_sites['Site Id'].astype(str).str.strip().str.upper()
df_merged = pd.merge(df_events, df_sites, left_on='site_name_clean', right_on='Site Id_clean', how='inner')

current = set(df_merged['Site Id'].str.upper().unique())
last = load_last_state()

new_off = current - last
recov = last - current
now = datetime.now().strftime("%Y-%m-%d %H:%M")

if not last:
    send_push(f"REON Started - {len(current)} Offline", f"First run {now}\nTotal: {len(current)}\nAb se sirf NEW ka alert ayega")
else:
    if new_off:
        df_new = df_merged[df_merged['Site Id'].str.upper().isin(new_off)].drop_duplicates('Site Id').head(10)
        details = "\n".join([f"- {r['Site Id']} ({r['Sub Region']})" for _,r in df_new.iterrows()])
        send_push(f"🚨 {len(new_off)} NEW Offline!", f"{len(new_off)} NEW @ {now}\n{details}")
    if recov:
        send_push(f"✅ {len(recov)} Online!", f"{len(recov)} Back Online @ {now}\n" + "\n".join(list(recov)[:10]))

save_state(current)
print(f"Done. Current:{len(current)} New:{len(new_off)} Recov:{len(recov)}")
