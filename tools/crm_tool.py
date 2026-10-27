#!/usr/bin/env python3
"""CRM tool for the email-agent skill. The ONLY thing that writes the CRM.

Two files (split 2026-10-19):
  {crm_dir}/contacts.json          MASTER: replied AND had a confirmed call (tier=master)
  {crm_dir}/contacts_archive.json  everyone else (tier=archive) with a `state`:
      active      outreach in flight, follow-up window open
      replied     replied but no call yet (warm; never auto-swept)
      dead        swept / bounced / no_response
      never_sent  drafted but never sent (OK to contact fresh later)

Every dedupe goes through is_known(), which checks BOTH files. Never read
contacts.json alone to decide whether someone is new.

Subcommands:
  brief                        session-start status
  is-known EMAIL [...]         dedupe check across both files (exit 1 if any known)
  add FILE.json                add new outreach contact(s) to archive (refuses known)
  sync-targets [--since D]     contacts + Gmail query batches for sync mode
  apply FILE.json              apply an APPROVED batch of changes
  promote FILE.json            move archive -> master with call evidence (approved)
  mark-processed ID... [--finish]
  followups [--days N]         archive/active due a follow-up (max 2 each)
  stale [--days N]             archive/active quiet N+ days -> sweep candidates
  log-followup KEY [--draft-id X]
  dupes
"""
import argparse
import json
import shutil
import sys
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

def _crm_root():
    """CRM dir: $EMAIL_AGENT_CRM_DIR, else profile.json paths.crm_dir, else ~/EmailCRM."""
    import os
    env = os.environ.get("EMAIL_AGENT_CRM_DIR")
    if env:
        return Path(env).expanduser()
    prof = Path(__file__).resolve().parent.parent / "profile.json"
    if prof.exists():
        d = json.loads(prof.read_text()).get("paths", {}).get("crm_dir")
        if d:
            return Path(d).expanduser()
    return Path.home() / "EmailCRM"


ROOT = _crm_root()
MASTER = ROOT / "contacts.json"
ARCHIVE = ROOT / "contacts_archive.json"
STATE = ROOT / "gmail_sync_state.json"
BACKUPS = ROOT / "backups"

STATES = {"active", "replied", "dead", "never_sent"}
STATUSES = {"drafted", "no_reply", "followed_up", "bounce_fixed", "replied", "call_done",
            "converted", "bounced", "bounce_dead", "no_response", "contact"}
MAX_FOLLOWUPS = 2
KEEP_BACKUPS = 5


# ---------------------------------------------------------------- storage

def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def load(path):
    return json.loads(path.read_text()) if path.exists() else []


def load_all():
    return load(MASTER), load(ARCHIVE)


def _backup(path):
    BACKUPS.mkdir(parents=True, exist_ok=True)
    dest = BACKUPS / f"{path.stem}.backup-{date.today().isoformat()}.json"
    if path.exists() and not dest.exists():
        shutil.copy2(path, dest)
    olds = sorted(BACKUPS.glob(f"{path.stem}.backup-*.json"))
    for old in olds[:-KEEP_BACKUPS]:
        old.unlink()


def save(path, data):
    _backup(path)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(path)


def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"last_sync": None, "processed_message_ids": []}


def save_state(state):
    STATE.write_text(json.dumps(state, indent=2))


def touch(c, action, detail=""):
    ap = c.setdefault("autopilot", {"history": []})
    ap["last_touched"] = now_iso()
    ap.setdefault("history", []).append({"ts": now_iso(), "action": action, "detail": detail})


def parse_day(s):
    try:
        return date.fromisoformat(str(s)[:10]) if s else None
    except ValueError:
        return None


def emails_of(c):
    return {e.lower() for e in [c.get("email"), *c.get("alt_emails", [])] if e}


def last_activity(c):
    days = [parse_day(c.get(k)) for k in ("last_contact", "sent_at", "follow_up_drafted_at", "drafted_at")]
    for h in (c.get("autopilot") or {}).get("history", []):
        if h.get("action", "").startswith(("sent", "followup", "agent:")):
            days.append(parse_day(h.get("ts")))
    days = [d for d in days if d]
    return max(days) if days else None


# ---------------------------------------------------------------- dedupe

def is_known(email, master=None, archive=None):
    """Return (tier, contact) if email is anywhere in the CRM, else (None, None)."""
    if master is None:
        master, archive = load_all()
    e = (email or "").lower().strip()
    for tier, rows in (("master", master), ("archive", archive)):
        for c in rows:
            if e in emails_of(c):
                return tier, c
    return None, None


def find(rows, key):
    k = key.lower()
    for field in ("id",):
        hits = [c for c in rows if c.get(field) == key or (c.get(field) or "").startswith(key)]
        if hits:
            return hits
    hits = [c for c in rows if c.get("name", "").lower() == k]
    return hits or [c for c in rows if k in emails_of(c)]


# ---------------------------------------------------------------- commands

def cmd_brief(_):
    master, archive = load_all()
    today = date.today()
    st = {}
    for c in archive:
        st.setdefault(c.get("state"), []).append(c)
    state = load_state()
    print(f"MASTER (replied + call): {len(master)} | ARCHIVE: {len(archive)} "
          f"(active {len(st.get('active', []))}, replied {len(st.get('replied', []))}, "
          f"never_sent {len(st.get('never_sent', []))}, dead {len(st.get('dead', []))})")
    print(f"Last Gmail sync: {state.get('last_sync') or 'never'}")
    print("\nMASTER:")
    for c in sorted(master, key=lambda c: c.get("last_contact") or "", reverse=True):
        print(f"  {c['name']} | {c.get('company')} | last {c.get('last_contact')}")
    if st.get("replied"):
        print("\nREPLIED, NO CALL YET (warm, worth a nudge):")
        for c in st["replied"]:
            print(f"  {c['name']} | {c.get('company')}")
    due = [c for c in st.get("active", []) if c.get("follow_up_count", 0) < MAX_FOLLOWUPS
           and (last_activity(c) and (today - last_activity(c)).days >= 7)]
    if due:
        print(f"\nFOLLOW-UPS POSSIBLE: {len(due)} active threads quiet 7+ days (run `followups`)")
    stale = [c for c in st.get("active", []) if last_activity(c) and (today - last_activity(c)).days >= 45]
    if stale:
        print(f"SWEEP: {len(stale)} active threads quiet 45+ days (run `stale`)")
    if (state.get("last_sync") or "0") < (today - timedelta(days=3)).isoformat():
        print("\nTIP: Gmail sync is 3+ days old. Run sync before trusting statuses.")


def cmd_is_known(a):
    master, archive = load_all()
    hit = False
    for e in a.emails:
        tier, c = is_known(e, master, archive)
        if tier:
            hit = True
            print(f"KNOWN  {e} -> {tier} | {c['name']} | {c.get('company')} | status {c.get('status')}"
                  f"{' | state ' + c['state'] if c.get('state') else ''}")
        else:
            print(f"NEW    {e}")
    sys.exit(1 if hit else 0)


def cmd_add(a):
    """FILE: [{name, email, company, role, email_type, gmail_draft_id, hook_used, cc, notes, ...}]"""
    rows = json.loads(Path(a.file).read_text())
    master, archive = load_all()
    added, refused = [], []
    for r in rows:
        tier, c = is_known(r["email"], master, archive)
        if tier:
            refused.append(f"{r['email']}: already in {tier} as {c['name']}")
            continue
        rec = {"id": str(uuid.uuid4()), "linkedin_url": None, "role": "", "cc": [], "notes": "",
               "gmail_draft_id": None, "gmail_thread_id": None, "hook_used": None, **r,
               "tier": "archive", "state": "active", "status": "drafted",
               "sent_at": None, "drafted_at": now_iso(), "follow_up_count": 0,
               "follow_up_due": (date.today() + timedelta(days=7)).isoformat()}
        touch(rec, "agent:add", r.get("email_type", ""))
        archive.append(rec)
        added.append(f"{rec['name']} <{rec['email']}>")
    if added:
        save(ARCHIVE, archive)
    print("ADDED:\n  " + ("\n  ".join(added) or "(none)"))
    if refused:
        print("REFUSED (dedupe):\n  " + "\n  ".join(refused))


def cmd_sync_targets(a):
    master, archive = load_all()
    state = load_state()
    since = a.since or state.get("last_sync")
    bound = "after:" + since.replace("-", "/") if since else "newer_than:120d"
    targets = [dict(tier="master", **{k: c.get(k) for k in ("id", "name", "company", "email", "status")}) for c in master]
    targets += [dict(tier="archive", **{k: c.get(k) for k in ("id", "name", "company", "email", "status", "state")})
                for c in archive if c.get("state") in ("active", "replied")]
    emails = sorted({e for c in master for e in emails_of(c)} |
                    {e for c in archive if c.get("state") in ("active", "replied") for e in emails_of(c)})
    queries = []
    for i in range(0, len(emails), 15):
        chunk = emails[i:i + 15]
        queries.append({"kind": "inbound", "q": "{" + " ".join(f"from:{e}" for e in chunk) + f"}} {bound} -in:drafts"})
        queries.append({"kind": "sent", "q": "in:sent {" + " ".join(f"to:{e}" for e in chunk) + f"}} {bound}"})
    queries.append({"kind": "bounce", "q": f"from:mailer-daemon {bound}"})
    queries.append({"kind": "calendar", "q": "Professional Calendar list_events since last_sync (call evidence)"})
    print(json.dumps({"since": since, "targets": targets, "queries": queries}, indent=1))


def _locate(master, archive, key):
    hits = [("master", c) for c in find(master, key)] + [("archive", c) for c in find(archive, key)]
    return hits


def cmd_apply(a):
    """FILE: [{"id": ..., "status"?: ..., "state"?: ..., "signal": ..., "source": "subject (date)",
              "sent_at"?, "gmail_thread_id"?, "last_contact"?, "message_ids": [...]}]
    Moving someone INTO master is `promote`, not `apply`."""
    changes = json.loads(Path(a.file).read_text())
    master, archive = load_all()
    state = load_state()
    written, refused = [], []
    for ch in changes:
        hits = _locate(master, archive, ch["id"])
        if len(hits) != 1:
            refused.append(f"{ch['id']}: {len(hits)} matches")
            continue
        tier, c = hits[0]
        if ch.get("status") and ch["status"] not in STATUSES:
            refused.append(f"{c['name']}: invalid status {ch['status']}")
            continue
        if ch.get("state") and (tier == "master" or ch["state"] not in STATES):
            refused.append(f"{c['name']}: invalid state {ch['state']} for {tier}")
            continue
        old = (c.get("status"), c.get("state"))
        for k in ("status", "state", "sent_at", "gmail_thread_id", "gmail_message_id", "last_contact", "email"):
            if ch.get(k):
                c[k] = ch[k]
        if old[0] == "drafted" and c.get("status") in ("no_reply", "followed_up") and ch.get("sent_at"):
            c["follow_up_due"] = (parse_day(ch["sent_at"]) + timedelta(days=7)).isoformat()
        note = f"{date.today()} sync: {ch.get('signal', 'update')} ({ch.get('source', '')})"
        c["notes"] = ((c.get("notes") or "") + " | " + note).strip(" |")
        touch(c, "agent:sync", f"{old} -> ({c.get('status')}, {c.get('state')}). {ch.get('signal', '')}")
        written.append(f"{c['name']} [{tier}]: {old} -> ({c.get('status')}, {c.get('state')})")
        for mid in ch.get("message_ids", []):
            if mid not in state["processed_message_ids"]:
                state["processed_message_ids"].append(mid)
    if written:
        save(MASTER, master)
        save(ARCHIVE, archive)
        save_state(state)
    print("WRITTEN:\n  " + ("\n  ".join(written) or "(none)"))
    if refused:
        print("REFUSED:\n  " + "\n  ".join(refused))


def cmd_promote(a):
    """FILE: [{"id": ..., "relationship": "...", "call_evidence": [{"source","id","date"}], "last_contact": ...}]
    Only for contacts the user approved as replied + confirmed call."""
    rows = json.loads(Path(a.file).read_text())
    master, archive = load_all()
    moved, refused = [], []
    for r in rows:
        hits = find(archive, r["id"])
        if len(hits) != 1:
            refused.append(f"{r['id']}: {len(hits)} archive matches")
            continue
        if not r.get("call_evidence"):
            refused.append(f"{hits[0]['name']}: no call_evidence")
            continue
        c = hits[0]
        archive.remove(c)
        c.pop("state", None)
        c.update(tier="master", status="call_done", relationship=r.get("relationship", ""),
                 call_evidence=r["call_evidence"], first_call=min(e["date"] for e in r["call_evidence"]),
                 last_contact=r.get("last_contact") or max(e["date"] for e in r["call_evidence"]))
        touch(c, "agent:promote", json.dumps(r["call_evidence"]))
        master.append(c)
        moved.append(c["name"])
    if moved:
        save(MASTER, master)
        save(ARCHIVE, archive)
    print("PROMOTED:\n  " + ("\n  ".join(moved) or "(none)"))
    if refused:
        print("REFUSED:\n  " + "\n  ".join(refused))


def cmd_mark_processed(a):
    state = load_state()
    seen = set(state["processed_message_ids"])
    for mid in a.ids:
        if mid not in seen:
            state["processed_message_ids"].append(mid)
            seen.add(mid)
    if a.finish:
        state["last_sync"] = date.today().isoformat()
    save_state(state)
    print(f"processed ids: {len(state['processed_message_ids'])}; last_sync: {state['last_sync']}")


def cmd_followups(a):
    _, archive = load_all()
    today = date.today()
    rows = []
    for c in archive:
        if c.get("state") not in ("active", "replied") or c.get("follow_up_count", 0) >= MAX_FOLLOWUPS:
            continue
        if c.get("status") in ("drafted", "bounced", "bounce_dead") or c.get("follow_up_draft_id"):
            continue
        la = last_activity(c)
        if la and a.days <= (today - la).days < a.max_days:
            rows.append(((today - la).days, c))
    rows.sort(key=lambda r: r[0])
    print("| # | Name | Company | State | Type | Days quiet | Follow-ups | Thread |")
    print("|---|---|---|---|---|---|---|---|")
    for i, (q, c) in enumerate(rows, 1):
        print(f"| {i} | {c['name']} | {c.get('company')} | {c.get('state')} | {c.get('email_type')} | {q} | "
              f"{c.get('follow_up_count', 0)} | {'yes' if c.get('gmail_thread_id') else 'NO'} |")
    print(f"\n{len(rows)} candidates (quiet {a.days}-{a.max_days - 1} days).")


def cmd_stale(a):
    _, archive = load_all()
    today = date.today()
    rows = [((today - last_activity(c)).days, c) for c in archive
            if c.get("state") == "active" and last_activity(c) and (today - last_activity(c)).days >= a.days]
    rows.sort(key=lambda r: -r[0])
    print("| # | id | Name | Company | Days quiet | Follow-ups | Proposed |")
    print("|---|---|---|---|---|---|---|")
    for i, (q, c) in enumerate(rows, 1):
        print(f"| {i} | {c['id'][:8]} | {c['name']} | {c.get('company')} | {q} | {c.get('follow_up_count', 0)} | dead / no_response |")
    print(f"\n{len(rows)} active threads quiet {a.days}+ days. Nothing written. Approve, then apply with "
          '{"state": "dead", "status": "no_response", "signal": "stale sweep"}.')


def cmd_log_followup(a):
    master, archive = load_all()
    hits = _locate(master, archive, a.key)
    if len(hits) != 1:
        sys.exit(f"{len(hits)} matches for {a.key}")
    tier, c = hits[0]
    if tier == "archive" and c.get("follow_up_count", 0) >= MAX_FOLLOWUPS:
        sys.exit(f"{c['name']} already has {MAX_FOLLOWUPS} follow-ups. No third. Offer sweep instead.")
    c["follow_up_count"] = c.get("follow_up_count", 0) + 1
    c["follow_up_drafted_at"] = now_iso()
    if a.draft_id:
        c["follow_up_draft_id"] = a.draft_id
    c["follow_up_due"] = (date.today() + timedelta(days=10)).isoformat()
    if c.get("status") == "no_reply":
        c["status"] = "followed_up"
    touch(c, "agent:followup", f"#{c['follow_up_count']} draft {a.draft_id or '-'}")
    save(MASTER if tier == "master" else ARCHIVE, master if tier == "master" else archive)
    print(f"{c['name']}: follow-up #{c['follow_up_count']} logged, next due {c['follow_up_due']}")


def cmd_dupes(_):
    master, archive = load_all()
    seen = {}
    for tier, rows in (("master", master), ("archive", archive)):
        for c in rows:
            for k in emails_of(c) | {f"{c['name'].lower()}|{(c.get('company') or '').lower()}"}:
                if k in seen:
                    t2, c2 = seen[k]
                    print(f"  {c2['name']} ({t2}, {c2['id'][:8]}) == {c['name']} ({tier}, {c['id'][:8]})")
                    break
                seen[k] = (tier, c)


def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest="cmd", required=True)
    s.add_parser("brief")
    t = s.add_parser("is-known"); t.add_argument("emails", nargs="+")
    t = s.add_parser("add"); t.add_argument("file")
    t = s.add_parser("sync-targets"); t.add_argument("--since")
    t = s.add_parser("apply"); t.add_argument("file")
    t = s.add_parser("promote"); t.add_argument("file")
    t = s.add_parser("mark-processed"); t.add_argument("ids", nargs="*"); t.add_argument("--finish", action="store_true")
    t = s.add_parser("followups"); t.add_argument("--days", type=int, default=7); t.add_argument("--max-days", type=int, default=45)
    t = s.add_parser("stale"); t.add_argument("--days", type=int, default=45)
    t = s.add_parser("log-followup"); t.add_argument("key"); t.add_argument("--draft-id")
    s.add_parser("dupes")
    a = p.parse_args()
    globals()["cmd_" + a.cmd.replace("-", "_")](a)


if __name__ == "__main__":
    main()
