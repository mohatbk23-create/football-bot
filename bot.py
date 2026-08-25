import os
import threading
import requests
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- 1. سيرفر Flask للحفاظ على عمل Render ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running live!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# --- 2. إعدادات التوكن والمفاتيح من متغيرات البيئة ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY", "73b64f33ca5c479fbccbf5cb9ef7aa9a")

# --- 3. اوامر التلغرام ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك! استخدم الأمر /matches لمعرفة مباريات اليوم.")

async def matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = "https://api.football-data.org/v4/matches"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        matches_list = data.get("matches", [])
        
        if not matches_list:
            await update.message.reply_text("لا توجد مباريات جارية أو محدودة اليوم.")
            return

        msg = "⚽ *مباريات اليوم:*\n\n"
        for m in matches_list[:10]:
            home = m["homeTeam"]["name"]
            away = m["awayTeam"]["name"]
            status = m["status"]
            msg += f"• {home} vs {away} ({status})\n"
            
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text("حدث خطأ أثناء جلب المباريات.")

# --- 4. تشغيل البوت والسيرفر ---
def main():
    if not TELEGRAM_TOKEN:
        print("ERROR: TELEGRAM_TOKEN environment variable is missing!")
        return

    # تشغيل سيرفر Flask في background thread
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

    # تشغيل تطبيق تلغرام
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("matches", matches))
    
    print("Starting bot polling...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
