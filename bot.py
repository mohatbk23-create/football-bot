import os
import logging
import threading
import requests
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# 1. إعداد خادم Flask للرد على Render
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Bot is active!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host='0.0.0.0', port=port)

# تشغيل السيرفر في خلفية النظام
threading.Thread(target=run_flask, daemon=True).start()

# 2. إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TELEGRAM_TOKEN = "8854322628:AAHaNUHbOwPOPfMpGaTnG6LXu27kCDmPy4K8"
FOOTBALL_API_KEY = "4b534deb375a4188948504292268eff3"

HEADERS = {'X-Auth-Token': FOOTBALL_API_KEY}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أهلاً بك في بوت نتائج المباريات! ⚽\n\n"
        "أرسل /matches لعرض نتائج ومباريات اليوم."
    )

async def get_matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_msg = await update.message.reply_text("جاري جلب نتائج ومباريات اليوم... ⏳")
    url = "https://api.football-data.org/v4/matches"
    
    try:
        response = requests.get(url, headers=HEADERS)
        data = response.json()
        matches = data.get('matches', [])

        if not matches:
            await status_msg.edit_text("لا توجد مباريات مسجلة اليوم في الدوريات الكبرى.")
            return

        text = "⚽ *مباريات اليوم والنتائج:*\n\n"
        for m in matches[:10]:
            home = m['homeTeam']['name']
            away = m['awayTeam']['name']
            status = m['status']
            
            if status == 'FINISHED':
                score_home = m['score']['fullTime']['home']
                score_away = m['score']['fullTime']['away']
                text += f"🔴 {home} {score_home} - {score_away} {away} (انتهت)\n"
            elif status == 'IN_PLAY':
                score_home = m['score']['fullTime']['home']
                score_away = m['score']['fullTime']['away']
                text += f"🟢 {home} {score_home} - {score_away} {away} (جارية الآن)\n"
            else:
                text += f"⚪ {home} vs {away} (لم تبدأ)\n"

        await status_msg.edit_text(text, parse_mode='Markdown')

    except Exception as e:
        logging.error(f"Error fetching matches: {e}")
        await status_msg.edit_text("حدث خطأ أثناء جلب البيانات.")

# 3. تشغيل البوت
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("matches", get_matches))
    app.run_polling(drop_pending_updates=True)
