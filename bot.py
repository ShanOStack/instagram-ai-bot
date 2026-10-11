import os
import sys
import time
import json
import random
import logging
from pathlib import Path
from dotenv import load_dotenv
import requests

# Ensure UTF-8 output on Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("InstagramAIBot")

# Load environment variables
ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(ENV_PATH)

INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME", "").strip()
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD", "").strip()
INSTAGRAM_SESSIONID = os.getenv("INSTAGRAM_SESSIONID", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", "90"))
AUTO_REPLY_DMS = os.getenv("AUTO_REPLY_DMS", "true").lower() == "true"
AUTO_REPLY_COMMENTS = os.getenv("AUTO_REPLY_COMMENTS", "false").lower() == "true"
OWNER_NAME = os.getenv("OWNER_NAME", "Shanteshwar").strip()
SESSION_FILE = Path(__file__).parent / "session.json"
HISTORY_FILE = Path(__file__).parent / "replied_history.json"


def load_history():
    """Load previously replied message/comment IDs."""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"dms": [], "comments": []}
    return {"dms": [], "comments": []}


def save_history(history):
    """Save replied message/comment IDs."""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save history: {e}")


def generate_ai_reply(sender_name: str, message_text: str, context_type: str = "DM") -> str:
    """Generate a smart reply using Google Gemini API."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured in .env")

    system_instruction = (
        f"You are 'Saantu ai', a smart, friendly personal AI assistant replying on behalf of {OWNER_NAME} on Instagram {context_type}. "
        "Goal: Be polite, natural, concise, and helpful (maximum 1-2 sentences). "
        "Language: Match the sender's language (Hindi, Hinglish, or English). "
        "Tone: Friendly, cool, and helpful. "
        f"Important: If someone asks about business, collaborations, or pricing, politely invite them to share their email or say that {OWNER_NAME} will follow up shortly."
    )

    url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    headers = {
        "Authorization": f"Bearer {GEMINI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": GEMINI_MODEL,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Incoming Instagram message from @{sender_name}:\n\"{message_text}\"\n\nWrite a short, natural reply:"}
        ],
        "temperature": 0.7,
        "max_tokens": 150
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        if response.status_code == 200:
            data = response.json()
            reply = data["choices"][0]["message"]["content"].strip()
            # Clean up potential quotation marks wrapper
            if (reply.startswith('"') and reply.endswith('"')) or (reply.startswith("'") and reply.endswith("'")):
                reply = reply[1:-1].strip()
            return reply
        else:
            logger.error(f"Gemini API returned HTTP {response.status_code}: {response.text}")
            return "Hey! Thanks for reaching out. I'll get back to you shortly!"
    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}")
        return "Hey! Thanks for your message. Will get back to you soon!"


def login_instagram():
    """Log in to Instagram and save session."""
    from instagrapi import Client

    global INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD
    if not INSTAGRAM_USERNAME or not INSTAGRAM_PASSWORD:
        print("\n==================================================")
        print("     Instagram Login Details Needed")
        print("==================================================")
        if not INSTAGRAM_USERNAME:
            INSTAGRAM_USERNAME = input("Enter your Instagram Username: ").strip()
        if not INSTAGRAM_PASSWORD:
            import getpass
            INSTAGRAM_PASSWORD = getpass.getpass("Enter your Instagram Password (hidden): ").strip()

        # Save to .env
        if INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD:
            try:
                lines = []
                if ENV_PATH.exists():
                    with open(ENV_PATH, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                new_lines = []
                has_user = False
                has_pass = False
                for line in lines:
                    if line.startswith("INSTAGRAM_USERNAME="):
                        new_lines.append(f"INSTAGRAM_USERNAME={INSTAGRAM_USERNAME}\n")
                        has_user = True
                    elif line.startswith("INSTAGRAM_PASSWORD="):
                        new_lines.append(f"INSTAGRAM_PASSWORD={INSTAGRAM_PASSWORD}\n")
                        has_pass = True
                    else:
                        new_lines.append(line)
                if not has_user:
                    new_lines.insert(0, f"INSTAGRAM_USERNAME={INSTAGRAM_USERNAME}\n")
                if not has_pass:
                    new_lines.insert(1, f"INSTAGRAM_PASSWORD={INSTAGRAM_PASSWORD}\n")
                with open(ENV_PATH, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
                print(f"[+] Credentials saved to .env!\n")
            except Exception as e:
                logger.warning(f"Could not save to .env: {e}")

    if not INSTAGRAM_USERNAME or not INSTAGRAM_PASSWORD:
        print("\n[!] Username and Password cannot be empty!\n")
        sys.exit(1)

    cl = Client()
    # Randomize device settings slightly to appear natural
    cl.delay_range = [2, 5]

    # 1. Try loading saved session
    if SESSION_FILE.exists():
        logger.info(f"Loading existing session from {SESSION_FILE}...")
        try:
            cl.load_settings(SESSION_FILE)
            if cl.user_id:
                logger.info("Session valid! Logged in successfully.")
                return cl
        except Exception as e:
            logger.warning(f"Existing session invalid ({e}). Refreshing...")

    # 2. Try sessionid cookie if provided
    global INSTAGRAM_SESSIONID
    if INSTAGRAM_SESSIONID:
        logger.info("Logging in using Instagram sessionid cookie...")
        try:
            cl.login_by_sessionid(INSTAGRAM_SESSIONID)
            cl.dump_settings(SESSION_FILE)
            logger.info(f"Login successful via sessionid! Session saved to {SESSION_FILE}.")
            return cl
        except Exception as e:
            logger.warning(f"Sessionid login failed ({e}). Falling back to username/password...")

    # 3. Try standard login
    logger.info(f"Logging in as @{INSTAGRAM_USERNAME}...")
    try:
        cl.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
        cl.dump_settings(SESSION_FILE)
        logger.info(f"Login successful! Session saved to {SESSION_FILE}.")
        return cl
    except Exception as e:
        error_str = str(e)
        logger.error(f"Instagram login failed: {error_str}")

        if "out of date" in error_str.lower() or "challenge" in error_str.lower():
            print("\n" + "="*60)
            print(" [!] Meta Security: Direct password login is blocked by Instagram.")
            print(" Iske liye aapko apne browser se 'sessionid' cookie daalni hogi.")
            print(" Kaise milegi (Sirf 30 seconds):")
            print("  1. Apne Chrome ya Edge me https://www.instagram.com open karein.")
            print("  2. Keyboard par F12 dabayein -> 'Application' tab par click karein.")
            print("  3. Left side me 'Cookies' -> 'https://www.instagram.com' par click karein.")
            print("  4. 'sessionid' naam ki cookie ki VALUE copy kar lijiye.")
            print("="*60 + "\n")

            entered_sessionid = input("Paste your Instagram 'sessionid' here: ").strip()
            if entered_sessionid:
                INSTAGRAM_SESSIONID = entered_sessionid
                # Save to .env
                try:
                    with open(ENV_PATH, "a", encoding="utf-8") as f:
                        f.write(f"\nINSTAGRAM_SESSIONID={entered_sessionid}\n")
                except Exception:
                    pass
                try:
                    cl.login_by_sessionid(entered_sessionid)
                    cl.dump_settings(SESSION_FILE)
                    logger.info(f"Login successful via sessionid! Session saved to {SESSION_FILE}.")
                    return cl
                except Exception as ex:
                    print(f"\n[!] Session ID login failed: {ex}\n")
                    sys.exit(1)

        raise e


def process_unread_dms(cl, history):
    """Check unread DM threads and send AI auto-replies."""
    try:
        # Fetch recent 10 direct message threads
        threads = cl.direct_threads(amount=10)
        user_id = str(cl.user_id)

        for thread in threads:
            if not thread.messages:
                continue

            last_msg = thread.messages[0]
            # Ignore messages sent by ourselves
            if str(last_msg.user_id) == user_id:
                continue

            msg_id = str(last_msg.id)
            if msg_id in history.get("dms", []):
                continue

            # Check if this thread has multiple users (group chat)
            sender_user = next((u for u in thread.users if str(u.pk) == str(last_msg.user_id)), None)
            sender_name = sender_user.username if sender_user else "user"

            msg_text = last_msg.text or ""
            if not msg_text.strip():
                # Maybe a photo, reel or voice note
                msg_text = "(shared a reel/post or media)"

            logger.info(f"New DM from @{sender_name}: '{msg_text}'")

            # Generate smart AI reply
            reply_text = generate_ai_reply(sender_name, msg_text, context_type="DM")
            final_reply = f'Saantu ai : "{reply_text}"'
            logger.info(f"Replying to @{sender_name} with: '{final_reply}'")

            # Human-like delay before sending
            time.sleep(random.uniform(4, 9))

            # Send reply
            cl.direct_send(final_reply, thread_ids=[thread.id])
            logger.info(f"Reply sent successfully to @{sender_name}!")

            # Record in history
            history["dms"].append(msg_id)
            # Keep history capped at 1000 items
            if len(history["dms"]) > 1000:
                history["dms"] = history["dms"][-1000:]
            save_history(history)

            # Random cooldown between replies
            time.sleep(random.uniform(3, 7))

    except Exception as e:
        logger.error(f"Error checking DMs: {e}")


def process_recent_comments(cl, history):
    """Check comments on the most recent 3 posts and reply with AI."""
    try:
        user_id = cl.user_id
        medias = cl.user_medias(user_id, amount=3)

        for media in medias:
            comments = cl.media_comments(media.id)
            for comment in comments:
                # Skip own comments
                if str(comment.user_id) == str(user_id):
                    continue

                comment_id = str(comment.pk)
                if comment_id in history.get("comments", []):
                    continue

                author = comment.user.username
                comment_text = comment.text

                logger.info(f"New Comment on post by @{author}: '{comment_text}'")

                reply_text = generate_ai_reply(author, comment_text, context_type="Post Comment")
                final_reply = f'Saantu ai : "{reply_text}"'
                logger.info(f"Replying to comment from @{author}: '{final_reply}'")

                time.sleep(random.uniform(5, 10))
                cl.comment_reply(comment_id, final_reply)
                logger.info(f"Comment reply posted to @{author}!")

                history["comments"].append(comment_id)
                if len(history["comments"]) > 1000:
                    history["comments"] = history["comments"][-1000:]
                save_history(history)

                time.sleep(random.uniform(4, 8))

    except Exception as e:
        logger.error(f"Error checking comments: {e}")


def test_ai_mode():
    """Test Gemini AI response generation locally without Instagram."""
    print("==================================================")
    print("      Testing Gemini AI Reply Generator")
    print("==================================================")
    test_messages = [
        ("rahul_99", "Bhai aapka course ka price kya hai? Details bhej do please."),
        ("priya_travels", "Loved your recent reel! Which camera do you use?"),
        ("amit_biz", "Hey, are you open for a brand collaboration this month?"),
        ("john_doe", "Hello, do you provide mentorship?")
    ]

    for sender, text in test_messages:
        print(f"\nIncoming from @{sender}: \"{text}\"")
        reply = generate_ai_reply(sender, text)
        print(f"-> Saantu ai : \"{reply}\"")
    print("\n[+] Gemini AI replies generated successfully!\n")


from http.server import HTTPServer, BaseHTTPRequestHandler
import threading


class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        html = "<html><body style='font-family:sans-serif;text-align:center;padding:50px;'><h1>🚀 Saantu AI Instagram Bot is Running 24/7!</h1><p>Status: Healthy & Active</p></body></html>"
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format, *args):
        pass


def start_health_server():
    port = int(os.environ.get("PORT", "7860"))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        logger.info(f"Cloud health server listening on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.warning(f"Could not bind health server on port {port}: {e}")


def run_bot_loop():
    """Run the continuous monitoring and auto-reply loop."""
    print("==================================================")
    print("      Starting Instagram AI Auto-Reply Bot")
    print(f"      Monitoring: DMs={AUTO_REPLY_DMS}, Comments={AUTO_REPLY_COMMENTS}")
    print(f"      Check interval: every {CHECK_INTERVAL_SECONDS} seconds")
    print("==================================================")

    # Start health server for 24/7 cloud hosts
    threading.Thread(target=start_health_server, daemon=True).start()

    cl = login_instagram()
    history = load_history()

    logger.info("Bot is active and listening for incoming messages...")

    while True:
        try:
            if AUTO_REPLY_DMS:
                process_unread_dms(cl, history)
            if AUTO_REPLY_COMMENTS:
                process_recent_comments(cl, history)
        except Exception as e:
            logger.error(f"Unexpected loop error: {e}")

        logger.info(f"Waiting {CHECK_INTERVAL_SECONDS}s before next check...")
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    if "--test-ai" in sys.argv:
        test_ai_mode()
    elif "--login" in sys.argv:
        login_instagram()
    else:
        run_bot_loop()
