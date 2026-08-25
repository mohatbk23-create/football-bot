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

# --- 2. إعدادات البوت والوظائف ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك في بوت نتائج المباريات المباشرة!")

async def matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚽ قائمة المباريات اليومية ستظهر هنا.")

async def post_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channel_id = "@DZFootballNews"
    text = "⚽ نتائج ومباريات اليوم المباشرة ⚽\n\nتابعوا القناة لتغطية شاملة!"
    await context.bot.send_message(chat_id=channel_id, text=text, parse_mode='Markdown')

def main():
    if not TELEGRAM_TOKEN:
        print("ERROR: TELEGRAM_TOKEN environment variable is missing!")
        return

    # تشغيل سيرفر Flask في الخلفية
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

    # تشغيل تطبيق تلغرام
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # تسجيل الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("matches", matches))
    application.add_handler(CommandHandler("post", post_to_channel))

    print("Starting bot polling...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
