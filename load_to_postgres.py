"""Load raw files into Postgres staging tables, deduplicating on source primary key.
Mirrors Orion's 'Python load/dedupe into Postgres' step."""
import json, csv, psycopg2
from pathlib import Path

CONN = dict(host="localhost", port=5433, dbname="orion_dw",
            user="orion", password="orion_local_pw")
RAW = Path("raw")

def connect():
    return psycopg2.connect(**CONN)

def load_zendesk(cur):
    rows = json.load(open(RAW/"zendesk"/"tickets.json"))
    cur.execute("DROP TABLE IF EXISTS raw_zendesk;")
    cur.execute("""CREATE TABLE raw_zendesk (
        ticket_id text, campaign text, channel text, requester_email text,
        assignee_id text, created_at text, first_response_at text, solved_at text,
        status text, wait_seconds numeric, satisfaction_score numeric, reopened boolean);""")
    seen, deduped = set(), []
    for r in rows:  # dedupe on ticket_id, first occurrence wins
        if r["ticket_id"] in seen: continue
        seen.add(r["ticket_id"]); deduped.append(r)
    cur.executemany("""INSERT INTO raw_zendesk VALUES
        (%(ticket_id)s,%(campaign)s,%(channel)s,%(requester_email)s,%(assignee_id)s,
         %(created_at)s,%(first_response_at)s,%(solved_at)s,%(status)s,
         %(wait_seconds)s,%(satisfaction_score)s,%(reopened)s);""", deduped)
    return len(rows), len(deduped)

def load_intercom(cur):
    rows = json.load(open(RAW/"intercom"/"conversations.json"))
    cur.execute("DROP TABLE IF EXISTS raw_intercom;")
    cur.execute("""CREATE TABLE raw_intercom (
        conversation_id text, campaign text, medium text, contact_id text,
        admin_id text, created_at text, first_reply_at text, closed_at text,
        state text, time_to_first_reply_ms numeric, conversation_rating numeric,
        reopened_flag text);""")
    seen, deduped = set(), []
    for r in rows:
        if r["conversationId"] in seen: continue
        seen.add(r["conversationId"]); deduped.append(r)
    cur.executemany("""INSERT INTO raw_intercom VALUES
        (%(conversationId)s,%(campaign)s,%(medium)s,%(contactId)s,%(adminId)s,
         %(createdAt)s,%(firstReplyAt)s,%(closedAt)s,%(state)s,
         %(timeToFirstReplyMs)s,%(conversationRating)s,%(reopenedFlag)s);""", deduped)
    return len(rows), len(deduped)

def load_csv(cur, table, path, cols):
    cur.execute(f"DROP TABLE IF EXISTS {table};")
    cur.execute(f"CREATE TABLE {table} ({', '.join(c+' text' for c in cols)});")
    with open(path) as f:
        r = csv.DictReader(f)
        rows = [[row[c] for c in cols] for row in r]
    ph = ",".join(["%s"]*len(cols))
    cur.executemany(f"INSERT INTO {table} VALUES ({ph});", rows)
    return len(rows)

def main():
    conn = connect(); cur = conn.cursor()
    zt, zd = load_zendesk(cur)
    it, idd = load_intercom(cur)
    na = load_csv(cur, "raw_zoho_agents", RAW/"zoho"/"agents.csv",
                  ["zoho_employee_id","full_name","zendesk_agent_id","intercom_admin_id"])
    ns = load_csv(cur, "raw_sla_targets", RAW/"sla_targets.csv",
                  ["campaign","metric","target_value","effective_from"])
    conn.commit(); cur.close(); conn.close()
    print(f"zendesk : {zt} raw -> {zd} after dedupe ({zt-zd} dupes removed)")
    print(f"intercom: {it} raw -> {idd} after dedupe ({it-idd} dupes removed)")
    print(f"zoho agents: {na} | sla targets: {ns}")

if __name__ == "__main__":
    main()