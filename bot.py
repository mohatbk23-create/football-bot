import os
import threading
import requests
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. خادم Flask الوهمي لتجاوز فحص Render ---
app_web = Flask('')

@app_web.route('/')
def home():
    return "Bot is active and running live!"

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

# --- 3. استخرج ميديا تيك توك بدون علامة مائية ---
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

# --- 5. دالة النشر التلقائي للأخبار ---
async def auto_post_news(context: ContextTypes.DEFAULT_TYPE):
    try:
        news_text = (
            "⚽ *أخبار كرة القدم | DZ Football*\n\n"
            "📌 متابعة مستمرة لآخر التحديثات والأخبار الرياضية اليومية.\n\n"
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

# --- 6. دالة النشر التلقائي للفيديوهات ---
async def auto_post_tiktok(context: ContextTypes.DEFAULT_TYPE):
    sample_tiktok_url = "https://www.tiktok.com/@tiktok/video/7000000000000000000" 
    video_url = get_clean_tiktok_url(sample_tiktok_url)
    if video_url:
        try:
            await context.bot.send_video(
                chat_id=CHANNEL_ID,
                video=video_url,
                caption="🎥 *لقطة اليوم الكروية من تيك توك* ⚽\n\n#كرة_قدم #DZFootballNews",
                reply_markup=get_channel_buttons(),
                parse_mode='Markdown'
            )
        except Exception as e:
            print(f"Error auto posting video: {e}")

# --- 7. دالة استقبال الروابط في الخاص ---
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
        await update.message.reply_text("أهلاً بك! أرسل لي رابط فيديو من تيك توك لتحميله بدون علامة مائية.")

# --- 8. نقطة الانطلاق والجدولة التلقائية ---
if __name__ == '__main__':
    keep_alive()
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    job_queue = app.job_queue
    job_queue.run_repeating(auto_post_news, interval=3600, first=10)
    job_queue.run_repeating(auto_post_tiktok, interval=10800, first=30)

    # إلغاء أي اتصال قديم فور التشغيل لتفادي خطأ 409
    app.run_polling(drop_pending_updates=True)
