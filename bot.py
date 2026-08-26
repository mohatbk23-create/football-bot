import os
import threading
import requests
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- 1. خادم Flask الوهمي لتجاوز فحص Render وتحقيق حالة Live ---
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

# --- 2. إعدادات المتغيرات والمعرفات ---
TOKEN = os.environ.get("BOT_TOKEN")
# استبدل المعرف أدناه بيوزر قناتك على تليغرام مع رمز @
CHANNEL_ID = "@DZFootballNews"

# --- 3. استخراج ميديا تيك توك بدون علامة مائية ---
def get_clean_tiktok_url(tiktok_url):
    try:
        api_url = f"https://api.douyin.wtf/api?url={tiktok_url}"
        response = requests.get(api_url, timeout=10).json()
        return response.get("nwm_video_url")
    except Exception as e:
        print(f"Error fetching TikTok video: {e}")
        return None

# --- 4. أوامر البوت ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "مرحباً بك في بوت كرة القدم والتغطية الرياضية! ⚽\n\n"
        "البرامج والأوامر المتاحة:\n"
        "• /post_text نص المنشور : لنشر خبر نصي في القناة.\n"
        "• /post_tiktok رابط_الفيديو : لتنزيل فيديو تيك توك بدون علامة مائية ونشره مباشرة في القناة."
    )
    await update.message.reply_text(welcome_text)

async def post_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_to_post = " ".join(context.args)
    if not text_to_post:
        await update.message.reply_text("⚠️ يرجى كتابة النص بعد الأمر، مثال:\n`/post_text عاجل: فوز الفريق اليوم بنتيجة 2-0`", parse_mode='Markdown')
        return

    try:
        await context.bot.send_message(chat_id=CHANNEL_ID, text=text_to_post)
        await update.message.reply_text("✅ تم نشر الخبر النصي في القناة بنجاح!")
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ أثناء النشر: {str(e)}")

async def post_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ يرجى إرسال رابط تيك توك بعد الأمر، مثال:\n`/post_tiktok https://vm.tiktok.com/XXXX/`", parse_mode='Markdown')
        return

    tiktok_url = context.args[0]
    msg = await update.message.reply_text("⏳ جاري تنزيل الفيديو بدون علامة مائية ونشره في القناة...")

    video_url = get_clean_tiktok_url(tiktok_url)

    if not video_url:
        await msg.edit_text("❌ فشل جلب الفيديو. تأكد من صحة الرابط أو حاول لاحقاً.")
        return

    try:
        await context.bot.send_video(
            chat_id=CHANNEL_ID,
            video=video_url,
            caption="🎥 *لقطة اليوم من تيك توك* ⚽\n\n#كرة_قدم #تغطية_خاصة",
            parse_mode='Markdown'
        )
        await msg.edit_text("✅ تم نشر الفيديو في القناة بنجاح وبدون علامة مائية!")
    except Exception as e:
        await msg.edit_text(f"❌ حدث خطأ أثناء رفع الفيديو للقناة: {str(e)}")

# --- 5. نقطة انطلاق البوت ---
if __name__ == '__main__':
    keep_alive()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("post_text", post_text))
    app.add_handler(CommandHandler("post_tiktok", post_tiktok))

    app.run_polling()
