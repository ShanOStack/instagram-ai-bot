# Instagram AI Auto-Reply Bot (Google Gemini Powered)

A smart, local Python automation bot that monitors incoming Instagram Direct Messages (DMs) and post comments, and automatically sends polite, human-like, contextual responses using Google Gemini AI.

---

## Features
- **AI-Powered Replies:** Uses Google Gemini (`gemini-3.5-flash-lite`) to read incoming DMs and generate smart, polite replies in Hindi, Hinglish, or English.
- **Session Persistence:** Saves your Instagram session to `session.json` so you do not need to log in repeatedly.
- **Duplicate Prevention:** Tracks replied messages in `replied_history.json` so the bot never replies twice to the same message.
- **Anti-Ban Safety:** Incorporates randomized human-like delays (4–10 seconds) between actions and checks every 90 seconds.
- **One-Click Desktop Launcher:** Start or configure directly using `InstagramBot.bat` on your Desktop.

---

## How to Use

1. Double-click **`InstagramBot.bat`** (or `InstagramBot.lnk`) on your Desktop.
2. Select **`[3] Set/Update Instagram Username & Password`** and enter your credentials.
3. Select **`[2] Test AI Reply Generator`** to see sample Gemini responses in action.
4. Select **`[1] Start Instagram Auto-Reply Bot`** to begin live monitoring!

---

## Safety Recommendations
- Instagram restricts aggressive bot activity. The bot is pre-configured with a safe 90-second polling interval and human delays.
- If you have 2-Factor Authentication (2FA) enabled on Instagram, the terminal will prompt you to enter the 6-digit verification code sent to your phone/authenticator app during first login.
