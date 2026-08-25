import os
import threading
import requests
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# إنشاء سيرفر Flask مصغر لمنع السيرفر من التوقف
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is active!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# جلب المتغيرات من إعدادات البيئة
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY", "2ccfae1d483246308a7a844723a15bc3")

def get_matches_data():
    url = "https://api.football-data.org/v4/matches"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    try:
        res = requests.get(url, headers=headers)
        data = res.json()
        matches = data.get("matches", [])
        if not matches:
            return "⚽ لا توجد مباريات مجدولة اليوم."
        
        msg = "⚽ مباريات اليوم ⚽\n\n"
        for m in matches[:10]:
            home = m.get("homeTeam", {}).get("shortName", "فريق 1")
            away = m.get("awayTeam", {}).get("shortName", "فريق 2")
            status = m.get("status", "")
            msg += f"▪️ {home} vs {away} ({status})\n"
        return msg
    except Exception:
        return "⚠️ تعذر جلب البيانات حالياً."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك! استخدم الأمر /matches لمعرفة مباريات اليوم.")

async def matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = get_matches_data()
    await update.message.reply_text(text, parse_mode='Markdown')

def main():
    if not TELEGRAM_TOKEN:
        print("TELEGRAM_TOKEN IS MISSING!")
        return

    # تشغيل سيرفر الويب في خلفية النظام
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

    # تشغيل البوت
    app_bot = Application.builder().token(TELEGRAM_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("matches", matches))
    
    app_bot.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
