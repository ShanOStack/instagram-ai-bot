import os
import sys
import json
from pathlib import Path

ENV_PATH = Path(__file__).parent / ".env"
HISTORY_PATH = Path(__file__).parent / "replied_history.json"


def update_credentials():
    print("==================================================")
    print("       Instagram Login Credentials Setup")
    print("==================================================")
    print("Note: Credentials are saved locally on your laptop in .env only.\n")

    username = input("Enter your Instagram Username: ").strip()
    if not username:
        print("[!] Username cannot be empty.")
        return

    import getpass
    password = getpass.getpass("Enter your Instagram Password (hidden): ").strip()
    if not password:
        print("[!] Password cannot be empty.")
        return

    print("\n[Optional] Agar Instagram direct password login block kare:")
    sessionid = input("Enter Instagram 'sessionid' cookie (press Enter to skip): ").strip()

    # Read existing .env
    lines = []
    if ENV_PATH.exists():
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

    new_lines = []
    has_user = False
    has_pass = False
    has_sess = False

    for line in lines:
        if line.startswith("INSTAGRAM_USERNAME="):
            new_lines.append(f"INSTAGRAM_USERNAME={username}\n")
            has_user = True
        elif line.startswith("INSTAGRAM_PASSWORD="):
            new_lines.append(f"INSTAGRAM_PASSWORD={password}\n")
            has_pass = True
        elif line.startswith("INSTAGRAM_SESSIONID="):
            if sessionid:
                new_lines.append(f"INSTAGRAM_SESSIONID={sessionid}\n")
                has_sess = True
        else:
            new_lines.append(line)

    if not has_user:
        new_lines.insert(0, f"INSTAGRAM_USERNAME={username}\n")
    if not has_pass:
        new_lines.insert(1, f"INSTAGRAM_PASSWORD={password}\n")
    if sessionid and not has_sess:
        new_lines.insert(2, f"INSTAGRAM_SESSIONID={sessionid}\n")

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    # If session.json exists from old user, remove it
    session_file = Path(__file__).parent / "session.json"
    if session_file.exists():
        session_file.unlink()

    print(f"\n[+] Successfully saved credentials for @{username}!")
    print("[+] Ready to start bot.\n")


def view_history():
    print("==================================================")
    print("           Recent Replied Messages")
    print("==================================================")
    if not HISTORY_PATH.exists():
        print("No messages have been replied to yet.")
        return

    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        dms = data.get("dms", [])
        comments = data.get("comments", [])
        print(f"Total DMs auto-replied: {len(dms)}")
        print(f"Total Comments auto-replied: {len(comments)}")
    except Exception as e:
        print(f"Error reading history: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "credentials":
        update_credentials()
    elif len(sys.argv) > 1 and sys.argv[1] == "history":
        view_history()
    else:
        print("Usage: python manage.py [credentials|history]")
