"""Orion demo — synthetic source generator. Two deliberately different shapes."""
import json, random, csv
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)
OUT = Path("raw")
for d in ["zendesk", "intercom", "zoho"]:
    (OUT / d).mkdir(parents=True, exist_ok=True)

CAMPAIGNS = {"CAMP_ZD": {"sla_answer_sec": 30}, "CAMP_IC": {"sla_answer_sec": 60}}
START = datetime(2026, 7, 1); DAYS = 60; ZD_ROWS = 3000; IC_ROWS = 2000
CHANNELS = ["chat", "email", "phone"]
ZD_STATUS = ["new", "open", "pending", "solved", "closed"]
IC_STATE = ["open", "snoozed", "closed"]

AGENTS = [{"zoho_employee_id": f"ZP{1000+i}", "full_name": f"Agent {i:02d}",
           "zendesk_agent_id": f"zd_{200+i}", "intercom_admin_id": f"{9000+i}"}
          for i in range(1, 9)]

def rand_ts(off):
    return START + timedelta(days=off, hours=random.randint(6,21),
                             minutes=random.randint(0,59), seconds=random.randint(0,59))

# ZENDESK — ticket-shaped, snake_case, seconds
zd = []
for n in range(ZD_ROWS):
    created = rand_ts(random.randint(0, DAYS-1)); a = random.choice(AGENTS)
    wait = random.choice([random.randint(2,120)]*9 + [None])
    fr = created + timedelta(seconds=wait) if wait is not None else None
    solved = fr + timedelta(minutes=random.randint(3,240)) if fr and random.random()>0.15 else None
    rec = {"ticket_id": f"ZD-{100000+n}", "campaign": "CAMP_ZD",
           "channel": random.choice(CHANNELS), "requester_email": f"cust{random.randint(1,900)}@example.com",
           "assignee_id": f"  {a['zendesk_agent_id']} " if random.random()<0.05 else a["zendesk_agent_id"],
           "created_at": created.isoformat(), "first_response_at": fr.isoformat() if fr else None,
           "solved_at": solved.isoformat() if solved else None, "status": random.choice(ZD_STATUS),
           "wait_seconds": wait, "satisfaction_score": random.choice([None,1,2,3,4,5]),
           "reopened": random.random()<0.08}
    if random.random()<0.02: rec["wait_seconds"] = -abs(random.randint(1,50))
    zd.append(rec)
zd += random.sample(zd, int(ZD_ROWS*0.03))
json.dump(zd, open(OUT/"zendesk"/"tickets.json","w"), indent=2)

# INTERCOM — conversation-shaped, camelCase, milliseconds
ic = []
for n in range(IC_ROWS):
    created = rand_ts(random.randint(0, DAYS-1)); a = random.choice(AGENTS)
    ms = random.choice([random.randint(2000,180000)]*9 + [None])
    fr = created + timedelta(milliseconds=ms) if ms else None
    closed = fr + timedelta(minutes=random.randint(2,300)) if fr and random.random()>0.2 else None
    ic.append({"conversationId": f"IC-{500000+n}", "campaign": "CAMP_IC",
               "medium": random.choice(["chat","email"]), "contactId": f"u{random.randint(1,700)}",
               "adminId": f"{a['intercom_admin_id']}  " if random.random()<0.05 else a["intercom_admin_id"],
               "createdAt": created.isoformat(), "firstReplyAt": fr.isoformat() if fr else None,
               "closedAt": closed.isoformat() if closed else None, "state": random.choice(IC_STATE),
               "timeToFirstReplyMs": ms, "conversationRating": random.choice([None,1,2,3,4,5]),
               "reopenedFlag": random.choice(["Y","N","N","N"])})
ic += random.sample(ic, int(IC_ROWS*0.03))
json.dump(ic, open(OUT/"intercom"/"conversations.json","w"), indent=2)

# ZOHO — agent master
with open(OUT/"zoho"/"agents.csv","w",newline="") as f:
    w = csv.writer(f); w.writerow(["zoho_employee_id","full_name","zendesk_agent_id","intercom_admin_id"])
    for a in AGENTS: w.writerow([a["zoho_employee_id"],a["full_name"],a["zendesk_agent_id"],a["intercom_admin_id"]])

# SLA config
with open(OUT/"sla_targets.csv","w",newline="") as f:
    w = csv.writer(f); w.writerow(["campaign","metric","target_value","effective_from"])
    for c,cfg in CAMPAIGNS.items(): w.writerow([c,"answer_seconds",cfg["sla_answer_sec"],"2026-01-01"])

print(f"Zendesk: {len(zd)} | Intercom: {len(ic)} | Agents: {len(AGENTS)}")