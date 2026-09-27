import pandas as pd, glob, os, requests, json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NTFY_TOPIC = "reon-spark-bahadur-95"

def send_push(title, msg):
    try:
        requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", data=msg.encode('utf-8'), headers={"Title": title, "Priority": "high"})
        print("Push sent")
    except Exception as e:
        print(f"Push fail: {e}")

# Find latest Events file (aapka wala naam bhi chalega)
files = glob.glob(os.path.join(BASE_DIR, "Events Report*.csv"))
if not files:
    send_push("REON Error", "Events Report file not found")
    exit(0)

latest = max(files, key=os.path.getctime)
df_events = pd.read_csv(latest, low_memory=False)
df_sites = pd.read_csv(os.path.join(BASE_DIR, "Sites List.csv"), low_memory=False)

df_events['site_name_clean'] = df_events['site_name'].astype(str).str.strip().str.upper()
df_sites['Site Id_clean'] = df_sites['Site Id'].astype(str).str.strip().str.upper()
df_merged = pd.merge(df_events, df_sites, left_on='site_name_clean', right_on='Site Id_clean', how='inner')

total = len(df_merged)
summary = f"REON {datetime.now().strftime('%Y-%m-%d %H:%M')} - Total Offline: {total}\n"
for sub, cnt in df_merged['Sub Region'].value_counts().items():
    summary += f"{sub}: {cnt}, "

print(summary)
send_push(f"REON - {total} Offline", summary[:4000])
