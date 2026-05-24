"""
Calmark Appointment Monitor – GitHub Actions Version
מתריע בטלגרם כשמתפנה תור. רץ פעם אחת ויוצא (GitHub Actions מפעיל אותו על לוח זמנים)
"""

import os
import requests
import json
from datetime import datetime

# =============================================
# הגדרות
# =============================================

# קוראים מ-Secrets של GitHub (אל תשים כאן ערכים אמיתיים!)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")

# תאריכים שמעניינים אותך (DD/MM/YYYY) – שנה כאן ידנית
TARGET_DATES = [
    "31/05/2026",
    "01/06/2026",
    
]

# =============================================
# קוד – אל תשנה
# =============================================

API_URL     = "https://calmark.io/Pages/Page.aspx/GetTimeForAppointment"
BUSINESS_ID = 28221
SERVICE_IDS = [145034]
BOOKING_URL = "https://calmark.io/p/KdEKr"

HEADERS = {
    "Content-Type": "application/json; charset=utf-8",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://calmark.io",
    "Referer": BOOKING_URL,
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
}


def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    r = requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }, timeout=10)
    r.raise_for_status()
    print("📨 הודעת טלגרם נשלחה")


def get_slots_for_date(date_str: str) -> list:
    now_time = datetime.now().strftime("%H:%M")
    payload = {
        "businessId": BUSINESS_ID,
        "services":   SERVICE_IDS,
        "date":       f"{date_str} {now_time}",
        "waitingList": False
    }
    r = requests.post(API_URL, headers=HEADERS, json=payload, timeout=15)
    r.raise_for_status()
    data = r.json()
    raw = json.loads(data["d"])
    slots_raw = raw[0] if raw and isinstance(raw[0], list) else []
    day, month, year = date_str.split("/")
    prefix = f"{year}-{month}-{day}"
    return [s for s in slots_raw if s.startswith(prefix)]


def format_alert(found: dict) -> str:
    msg = "🚨 <b>התפנה תור ב-Calmark!</b>\n\n"
    for date, slots in found.items():
        msg += f"📅 <b>{date}</b>\n"
        for s in slots:
            t = s.split("T")[1][:5]
            msg += f"   ⏰ {t}\n"
        msg += "\n"
    msg += f'🔗 <a href="{BOOKING_URL}">לחץ לקביעת תור</a>'
    return msg


def main():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ חסרים TELEGRAM_BOT_TOKEN או TELEGRAM_CHAT_ID ב-Secrets")
        return

    print(f"[{datetime.now().strftime('%H:%M:%S')}] בודק תורים...")
    found = {}
    for date in TARGET_DATES:
        try:
            slots = get_slots_for_date(date)
            if slots:
                found[date] = slots
                print(f"  ✅ {date}: {len(slots)} תורים")
            else:
                print(f"  ❌ {date}: אין תורים")
        except Exception as e:
            print(f"  ⚠️  שגיאה ב-{date}: {e}")

    if found:
        send_telegram(format_alert(found))
    else:
        print("אין תורים פנויים – לא שולח הודעה")


if __name__ == "__main__":
    main()
