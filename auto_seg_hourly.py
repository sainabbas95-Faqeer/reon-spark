import pandas as pd, glob, os, requests, json
from datetime import datetime
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "last_alarm_state.json")
TOPIC = "reon-spark-bahadur-95"
def load():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE,'r') as f: return set(json.load(f))
    return set()
def save(s):
    with open(STATE_FILE,'w') as f: json.dump(list(s),f)
def push(t,m): requests.post(f"https://ntfy.sh/{TOPIC}", data=m.encode('utf-8'), headers={"Title": t, "Priority": "high"})
files = glob.glob(os.path.join(BASE_DIR, "Events Report*.csv"))
latest = max(files, key=os.path.getctime)
df_e = pd.read_csv(latest, low_memory=False)
df_s = pd.read_csv(os.path.join(BASE_DIR, "Sites List.csv"), low_memory=False)
df_e['clean'] = df_e['site_name'].astype(str).str.strip().str.upper()
df_s['clean'] = df_s['Site Id'].astype(str).str.strip().str.upper()
merged = pd.merge(df_e, df_s, left_on='clean', right_on='clean', how='inner')
cur = set(merged['Site Id'].str.upper())
last = load()
new = cur - last
rec = last - cur
now = datetime.now().strftime("%d/%m %H:%M")
if not last:
    push(f"REON Started - {len(cur)} Offline", f"First run {now}\nTotal: {len(cur)}\nAb se sirf NEW ka alert ayega")
else:
    if new:
        det = merged[merged['Site Id'].str.upper().isin(new)].drop_duplicates('Site Id').head(10)
        msg = "\n".join([f"- {r['Site Id']} ({r['Sub Region']})" for _,r in det.iterrows()])
        push(f"🚨 {len(new)} NEW Offline @ {now}", f"{msg}")
    if rec:
        push(f"✅ {len(rec)} Back Online @ {now}", "\n".join(list(rec)[:10]))
save(cur)
