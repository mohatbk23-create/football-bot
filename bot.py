import os
import threading
import requests
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. خادم Flask لإبقاء البوت شغالاً على Render ---
app_web = Flask('')

@app_web.route('/')
def home():
    return "Global Football Bot is Live!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run_web)
    t.daemon = True
    t.start()

# --- 2. الإعدادات والمعرفات ---
TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = "@DZFootballNews"

# --- 3. استخراج ميديا تيك توك بدون علامة مائية ---
def get_clean_tiktok_url(tiktok_url):
    try:
        api_url = f"https://api.douyin.wtf/api?url={tiktok_url}"
        response = requests.get(api_url, timeout=10).json()
        return response.get("nwm_video_url")
    except Exception as e:
        print(f"Error TikTok API: {e}")
        return None

# --- 4. الأزرار التفاعلية أسفل المنشورات ---
def get_channel_buttons():
    keyboard = [
        [
            InlineKeyboardButton("💬 تواصل معنا", url="https://t.me/YourUsername"),
            InlineKeyboardButton("📢 القناة الرسمية", url="https://t.me/DZFootballNews")
        ],
        [
            InlineKeyboardButton("📲 حساب التيك توك", url="https://tiktok.com/@YourAccount")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- 5. دالة النشر التلقائي لأبرز نتائج وتصنيفات الدوريات العالمية ---
async def auto_post_global_standings(context: ContextTypes.DEFAULT_TYPE):
    try:
        global_text = (
            "🌍 *ملخص تصنيف الدوريات العالمية والأدوار القادمة* ⚽\n\n"
            "🏴󠁧󠁢󠁥󠁮󠁧󠁿 *الدوري الإنجليزي الممتاز (Premier League):*\n"
            "text\n"
            "م | الفريق          | لعب | نقاط\n"
            "----------------------------------\n"
            "1 | مانشستر سيتي   | 38  | 91\n"
            "2 | آرسنال         | 38  | 89\n"
            "3 | ليفربول        | 38  | 82\n"
            "\n\n"
            "🇪🇸 *الدوري الإسباني (La Liga):*\n"
            "text\n"
            "م | الفريق          | لعب | نقاط\n"
            "----------------------------------\n"
            "1 | ريال مدريد      | 38  | 95\n"
            "2 | برشلونة        | 38  | 85\n"
            "3 | جيرونا         | 38  | 81\n"
            "\n\n"
            "🏆 *أدوار دوري أبطال أوروبا (Champions League):*\n"
            "text\n"
            "الدور       | المواجهة                | التوقيت\n"
            "----------------------------------------------\n"
            "نصف النهائي | ريال مدريد vs بايرن ميونخ | 21:00\n"
            "نصف النهائي | باريس vs بروسيا دورتموند | 21:00\n"
            "\n\n"
            "📌 يتم تحديث النتائج والتصنيفات العالمية بشكل دوري!"
        )
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=global_text,
            reply_markup=get_channel_buttons(),
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"Error auto posting global standings: {e}")

# --- 6. دالة النشر التلقائي للأخبار العالمية ---
async def auto_post_news(context: ContextTypes.DEFAULT_TYPE):
    try:
        news_text = (
            "⚽ *أخبار كرة القدم العالمية والتحليلات | DZ Football*\n\n"
            "📌 متابعة مستمرة لآخر التحديثات، الانتقالات، والمباريات العالمية والمحلية.\n\n"
            "🔴 اشترك وشارك القناة ليصلك كل جديد!"
        )
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=news_text,
            reply_markup=get_channel_buttons(),
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"Error auto posting news: {e}")

# --- 7. دالة استقبال الرسائل والروابط في الخاص ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "tiktok.com" in text:
        await update.message.reply_text("⏳ جاري تحميل الفيديو بدون علامة مائية...")
        video_url = get_clean_tiktok_url(text)
        if video_url:
            await update.message.reply_video(video=video_url, caption="✅ تم التحميل بنجاح بواسطة البوت!")
        else:
            await update.message.reply_text("❌ عذراً، تعذر تحميل الفيديو. تأكد من صحة الرابط.")
    else:
        welcome_text = (
            "أهلاً بك في بوت *DZ Football* الشامل! ⚽🌍\n\n"
            "🔹 *في القناة:* ننشر تلقائياً الأخبار، تصنيفات كافة الدوريات العالمية (الإنجليزي، الإسباني، الإيطالي، دوري الأبطال) ومواعيد الأدوار.\n"
            "🔹 *في الخاص:* أرسل لي أي رابط من تيك توك لتحميل الفيديو فوراً بدون علامة مائية."
        )
        await update.message.reply_text(welcome_text, parse_mode='Markdown')

# --- 8. نقطة الانطلاق والجدولة التلقائية ---
if __name__ == '__main__':
    keep_alive()
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    job_queue = app.job_queue
    
    # نشر الأخبار كل ساعة
    job_queue.run_repeating(auto_post_news, interval=3600, first=10)
    
    # نشر جدول الترتيب والأدوار العالمية كل 6 ساعات (21600 ثانية)
    job_queue.run_repeating(auto_post_global_standings, interval=21600, first=60)

    # إلغاء أي اتصال قديم فور التشغيل لتفادي خطأ 409
    app.run_polling(drop_pending_updates=True)
