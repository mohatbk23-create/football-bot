import os
import threading
import requests
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- 1. سيرفر Flask للحفاظ على عمل البوت في Render ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running live!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# --- 2. إعدادات البوت والـ API ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
FOOTBALL_API_KEY = "2ccfae1d483246308a7a844723a15bc3"  # مفتاحك جاهز هنا
CHANNEL_ID = "@DZFootballNews"

def get_live_matches():
    """جلب مباريات اليوم من Football-Data"""
    url = "https://api.football-data.org/v4/matches"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        matches = data.get("matches", [])
        
        if not matches:
            return "⚽ لا توجد مباريات كبرى مجدولة لهذا اليوم."
        
        text = "⚽ *مباريات ونتائج اليوم* ⚽\n\n"
        for match in matches[:8]:  # يعرض حتى 8 مباريات
            home_team = match["homeTeam"]["shortName"]
            away_team = match["awayTeam"]["shortName"]
            
            # محاولة جلب النتيجة إذا بدأت المباراة
            score_data = match.get("score", {}).get("fullTime", {})
            home_score = score_data.get("home")
            away_score = score_data.get("away")
            
            status = match["status"]
            # ترجمة بسيطة لحالة المباراة
            if status == "FINISHED": status_ar = "انتهت"
            elif status == "IN_PLAY": status_ar = "مباشر"
            elif status == "PAUSED": status_ar = "استراحة"
            elif status == "TIMED": status_ar = "لم تبدأ"
            else: status_ar = status

            if home_score is None:
                text += f"▪️ {home_team} vs {away_team} ({status_ar})\n"
            else:
                text += f"▪️ {home_team} {home_score} - {away_score} {away_team} ({status_ar})\n"
                
        text += "\nتابعوا القناة لتغطية مستمرة!"
        return text
    except Exception as e:
        return f"⚠️ لم نتمكن من تحديث المباريات حالياً."

# --- 3. أوامر البوت ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك! أنا أعمل الآن وأقوم بنشر نتائج المباريات تلقائياً.")

async def matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # عند إرسال /matches للبوت، سيرد بجدول المباريات
    results = get_live_matches()
    await update.message.reply_text(results)

# --- 4. دالة النشر التلقائي في القناة ---
async def auto_post_job(context: ContextTypes.DEFAULT_TYPE):
    results = get_live_matches()
    await context.bot.send_message(chat_id=CHANNEL_ID, text=results)

def main():
    if not TELEGRAM_TOKEN:
        print("ERROR: TELEGRAM_TOKEN is missing in Render environment!")
        return

    # تشغيل Flask
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

    # إعداد تطبيق تلغرام
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # تسجيل الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("matches", matches))

    # إعداد النشر التلقائي: النشر الأول بعد 10 ثوانٍ، ثم تكرار كل ساعة (3600 ثانية)
    job_queue = application.job_queue
    job_queue.run_repeating(auto_post_job, interval=3600, first=10)

    print("Starting bot...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
