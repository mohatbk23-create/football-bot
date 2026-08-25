import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
API_KEY = os.environ.get("RAPIDAPI_KEY")

HEADERS = {
    "Content-Type": "application/json",
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "free-football-api-data.p.rapidapi.com"
}

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
        url = "https://free-football-api-data.p.rapidapi.com/football-event-statistics"
        querystring = {"eventid": "12650707"}
        
        try:
            res = requests.get(url, headers=HEADERS, params=querystring).json()
            await query.edit_message_text("Data fetched successfully!")
        except Exception:
            await query.edit_message_text("Error fetching data. Check your RAPIDAPI_KEY in Render.")

    elif query.data == 'news':
        await query.edit_message_text("News feature working!")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()
