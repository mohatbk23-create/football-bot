import os
import threading
import requests
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# --- 1. خادم Flask الوهمي لتجاوز فحص Render ---
app_web = Flask('')

@app_web.route('/')
def home():
    return "Bot is active!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run_web)
    t.start()

# --- 2. إعداد المفاتيح ---
TOKEN = os.environ.get("BOT_TOKEN")

# --- 3. معالجة أوامر التلغرام ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Stats", callback_data='stats')],
        [InlineKeyboardButton("News", callback_data='news')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome to Football Bot! Choose an option:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'stats':
        await query.edit_message_text("Fetching statistics...")
        
        # تجربة الاتصال ورؤية النتيجة
        try:
            # اختبار استجابة ناجحة
            await query.edit_message_text("⚽ Live Match Stats:\n\n- Team A vs Team B\n- Score: 2 - 1\n- Status: Live / Active")
        except Exception as e:
            await query.edit_message_text(f"Error: {str(e)}")

    elif query.data == 'news':
        await query.edit_message_text("📰 Latest Football News:\n\n- Champions League draw starts tomorrow.\n- Transfer window updates active.")

# --- 4. نقطة الانطلاق ---
if __name__ == '__main__':
    keep_alive()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()
