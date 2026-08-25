import os
import logging
import threading
import requests
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- 1. إعداد سجلات الأخطاء (Logging) لمعالجة أي إشكال فوراً ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- 2. سيرفر Flask مصغر لحفظ عمل البوت على Render ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running continuously and smoothly!"

def run_flask():
    try:
        port = int(os.environ.get("PORT", 10000))
        app.run(host="0.0.0.0", port=port)
    except Exception as e:
        logger.error(f"Flask server error: {e}")

# --- 3. جلب المتغيرات والتهيئ الأمني ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY", "2ccfae1d483246308a7a844723a15bc3")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "@DZFootballNews")

def get_matches_summary():
    """جلب المباريات مع حماية كاملة ضد أخطاء الشبكة والـ API"""
    url = "https://api.football-data.org/v4/matches"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        
        # التأكد من صحة استجابة السيرفر
        if res.status_code != 200:
            logger.warning(f"API Returned status code: {res.status_code}")
            return "⚠️ تعذر جلب البيانات حالياً بسبب ضغط على خادم النتائج."

        data = res.json()
        matches = data.get("matches", [])
        
        if not matches:
            return "⚽ لا توجد مباريات كبرى مجدولة لهذا اليوم."
        
        msg = "⚽ جدول ونتائج مباريات اليوم ⚽\n\n"
        
        for m in matches[:12]:
            try:
                # استخراج اسم الفريق والحصول على الاسم القصير بأمان
                home = m.get("homeTeam", {}).get("shortName") or m.get("homeTeam", {}).get("name") or "فريق 1"
                away = m.get("awayTeam", {}).get("shortName") or m.get("awayTeam", {}).get("name") or "فريق 2"
                competition = m.get("competition", {}).get("name", "بطولة عامة")
                status = m.get("status", "")
                
                # استخراج النتيجة
                score_data = m.get("score", {}).get("fullTime", {})
                home_score = score_data.get("home")
                away_score = score_data.get("away")
                
                # حالات المباراة باللغة العربية
                status_map = {
                    "FINISHED": "🔚 انتهت",
                    "IN_PLAY": "🔴 جارٍ اللعب الآن",
                    "PAUSED": "⏸️ استراحة بين الشوطين",
                    "TIMED": "⏰ لم تبدأ بعد",
                    "SCHEDULED": "⏰ مجدولة"
                }
                status_text = status_map.get(status, f"📌 {status}")

                if home_score is not None and away_score is not None:
                    msg += f"🏆 {competition}\n▪️ {home} {home_score} - {away_score} {away_team}\n📊 الحالة: {status_text}\n\n"
                else:
                    msg += f"🏆 {competition}\n▪️ {home} vs {away}\n📊 الحالة: {status_text}\n\n"
            except Exception as item_err:
                logger.error(f"Error parsing match item: {item_err}")
                continue
                
        msg += "--- \n📢 تابعوا القناة لمزيد من التغطيات المباشرة!"
        return msg

    except requests.exceptions.RequestException as req_err:
        logger.error(f"Network error while fetching matches: {req_err}")
        return "⚠️ حدث خطأ في الاتصال بالسيرفر الرياضي، يرجى المحاولة لاحقاً."
    except Exception as e:
        logger.error(f"Unexpected error in get_matches_summary: {e}")
        return "⚠️ حدث خطأ غير متوقع أثناء معالجة النتائج."

# --- 4. أوامر تلغرام والمهمات التلقائية ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("أهلاً بك! البوت جاهز ويقوم بنشر إحصائيات ونتائج المباريات.\nاستخدم الأمر /matches لرؤية المباريات الآن.")
    except Exception as e:
        logger.error(f"Error in start command: {e}")

async def matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = get_matches_summary()
        await update.message.reply_text(text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error sending matches to user: {e}")

async def auto_post_job(context: ContextTypes.DEFAULT_TYPE):
    """وظيفة النشر التلقائي للقناة كل 30 دقيقة"""
    if not CHANNEL_ID:
        return
        
    try:
        text = get_matches_summary()
        await context.bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode='Markdown')
        logger.info("Successfully posted matches update to channel.")
    except Exception as e:
        logger.error(f"Failed to post to channel {CHANNEL_ID}: {e}")

def main():
    if not TELEGRAM_TOKEN:
        logger.critical("TELEGRAM_TOKEN IS MISSING! Stopping bot execution.")
        return

    # تشغيل سيرفر Flask في خيط منفصل (Thread)
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

    # إنشاء التطبيق
    app_bot = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # إضافة الأوامر
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("matches", matches))

    # ضبط جدولة النشر المباشر كل 30 دقيقة
    job_queue = app_bot.job_queue
    if job_queue:
        job_queue.run_repeating(auto_post_job, interval=1800, first=15)

    logger.info("Starting bot polling...")
    app_bot.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
