# tt — Command-Line Time Tracker

Simple time tracker for the terminal. Start, stop, and log tasks. Data stored in `~/.tt/`.

## Install

```bash
pip install -e /GithubAI/tt
```

Or run directly:

```bash
python3 /GithubAI/tt/tt.py start "Working on X"
```

## Usage

```
tt start "Task name"    Start tracking a task
tt stop                 Stop current task and log it
tt status               Show current task and elapsed time
tt log                  Show all logged time entries
tt log --today          Show today's entries only
```

## Data

Entries are stored as JSONL in `~/.tt/log.jsonl`. Current task state in `~/.tt/status.json`.
