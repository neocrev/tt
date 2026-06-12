#!/usr/bin/env python3
"""tt — simple time tracker for the command line. Start, stop, and log tasks."""

import json, os, sys, argparse
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path.home() / ".tt"
LOG_FILE = DATA_DIR / "log.jsonl"
STATUS_FILE = DATA_DIR / "status.json"

def ensure():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def now(): return datetime.now().isoformat(timespec="seconds")

def cmd_start(args):
    ensure()
    task = " ".join(args.task) if args.task else "untitled"
    if STATUS_FILE.exists():
        try:
            cur = json.loads(STATUS_FILE.read_text())
            if not args.force:
                print(f"tt: already tracking '{cur['task']}' (started {cur['start']})")
                print("  Use 'tt stop' first, or 'tt start --force' to override")
                return
            cmd_stop(args)
        except: pass
    STATUS_FILE.write_text(json.dumps({"task": task, "start": now()}))
    print(f"tt: started '{task}'")

def cmd_stop(args):
    ensure()
    if not STATUS_FILE.exists():
        print("tt: no active task. Use 'tt start <task>'")
        return
    try:
        cur = json.loads(STATUS_FILE.read_text())
    except: cur = {"task": "?", "start": now()}
    end = now()
    entry = {**cur, "end": end}
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    STATUS_FILE.unlink(missing_ok=True)
    dur = _duration(cur["start"], end)
    print(f"tt: stopped '{cur['task']}' ({dur})")

def cmd_status(args):
    if not STATUS_FILE.exists():
        print("tt: no active task")
        return
    try:
        cur = json.loads(STATUS_FILE.read_text())
    except:
        print("tt: status file corrupted")
        return
    dur = _duration(cur["start"], now())
    print(f"tt: tracking '{cur['task']}' for {dur} (since {cur['start']})")

def cmd_log(args):
    ensure()
    if not LOG_FILE.exists():
        print("tt: no log entries yet")
        return
    entries = []
    with open(LOG_FILE) as f:
        for line in f:
            line = line.strip()
            if line:
                try: entries.append(json.loads(line))
                except: pass
    if not entries:
        print("tt: no log entries")
        return
    # Filter by day if requested
    if args.today:
        today = datetime.now().strftime("%Y-%m-%d")
        entries = [e for e in entries if e.get("start","").startswith(today)]
    total = timedelta()
    print(f"{'Task':<30} {'Duration':<12} {'When':<20}")
    print("-" * 62)
    for e in entries:
        dur_s = _duration(e.get("start",""), e.get("end",""))
        d = _parse_dur(e.get("start",""), e.get("end",""))
        if d: total += d
        start_short = e.get("start","")[11:19] if e.get("start","") else "?"
        print(f"{e.get('task','?'):<30} {dur_s:<12} {start_short}")
    if total.total_seconds() > 0:
        h, r = divmod(int(total.total_seconds()), 3600)
        m, s = divmod(r, 60)
        print("-" * 62)
        print(f"{'Total':<30} {h}h {m}m {s}s")

def _duration(s, e):
    d = _parse_dur(s, e)
    if not d: return "?"
    h, r = divmod(int(d.total_seconds()), 3600)
    m, s = divmod(r, 60)
    if h: return f"{h}h {m}m"
    if m: return f"{m}m {s}s"
    return f"{s}s"

def _parse_dur(s, e):
    try:
        sd = datetime.fromisoformat(s)
        ed = datetime.fromisoformat(e)
        return ed - sd
    except: return None

def cmd_report(args):
    ensure()
    if not LOG_FILE.exists():
        print("tt: no log entries yet")
        return
    entries = []
    with open(LOG_FILE) as f:
        for line in f:
            line = line.strip()
            if line:
                try: entries.append(json.loads(line))
                except: pass
    if not entries:
        print("tt: no log entries")
        return
    today = datetime.now()
    week_ago = today - timedelta(days=7)
    week_entries = [e for e in entries if e.get("start","")[:10] >= week_ago.strftime("%Y-%m-%d")]
    if not week_entries:
        print("tt: no entries in the past 7 days")
        return
    tasks = {}
    for e in week_entries:
        task = e.get("task","untitled")
        d = _parse_dur(e.get("start",""), e.get("end",""))
        if d:
            tasks.setdefault(task, timedelta())
            tasks[task] += d
    total = sum(tasks.values(), timedelta())
    print(f"tt: weekly report ({week_ago.strftime('%b %d')} – {today.strftime('%b %d')})")
    print()
    for task, dur in sorted(tasks.items(), key=lambda x: -x[1].total_seconds()):
        h, r = divmod(int(dur.total_seconds()), 3600)
        m, s = divmod(r, 60)
        bar = "█" * min(int(h * 2 + m / 30), 30) or "▏"
        pct = dur.total_seconds() / total.total_seconds() * 100 if total.total_seconds() else 0
        print(f"  {bar}  {task:<28} {h}h {m}m ({pct:.0f}%)")
    print()
    h, r = divmod(int(total.total_seconds()), 3600)
    m, s = divmod(r, 60)
    print(f"  Total: {h}h {m}m across {len(tasks)} tasks")

def main():
    parser = argparse.ArgumentParser(
        description="tt — simple command-line time tracker.",
        epilog="Examples:\n  tt start \"Working on X\"\n  tt stop\n  tt status\n  tt log --today\n  tt log",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("start", help="Start tracking a task")
    p.add_argument("task", nargs="*", help="Task description")
    p.add_argument("--force", "-f", action="store_true", help="Force start, stop current task")
    p.set_defaults(func=cmd_start)

    p = sub.add_parser("stop", help="Stop tracking current task")
    p.set_defaults(func=cmd_stop)

    p = sub.add_parser("status", help="Show current task and elapsed time")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("log", help="Show time log")
    p.add_argument("--today", action="store_true", help="Show only today's entries")
    p.set_defaults(func=cmd_log)

    p = sub.add_parser("report", help="Show weekly summary of tracked time")
    p.set_defaults(func=cmd_report)

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        sys.exit(1)
    args.func(args)

if __name__ == "__main__":
    main()
