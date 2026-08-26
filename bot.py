import os
import threading
import requests
import logging
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. Logging Configuration ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- 2. Flask Keep-Alive Server ---
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

# --- 3. Bot & Channel Configuration ---
TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = "@DZFootballNews"

# --- 4. Bulletproof & HD TikTok Downloader ---
def get_clean_tiktok_url(tiktok_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, /',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    # Resolve shortened URLs (vt.tiktok.com)
    try:
        session = requests.Session()
        res_redirect = session.head(tiktok_url, allow_redirects=True, timeout=8, headers=headers)
        final_url = res_redirect.url
    except Exception:
        final_url = tiktok_url

    # Primary API: TikWM (HD quality, no compression)
    try:
        api1 = f"https://www.tikwm.com/api/?url={final_url}&hd=1"
        r1 = requests.get(api1, headers=headers, timeout=10).json()
        if r1.get("code") == 0 and r1.get("data"):
            data = r1["data"]
            return data.get("hdplay") or data.get("play")
    except Exception as e:
        logging.error(f"TikWM Primary HD API Error: {e}")

    # Backup API 1: Douyin/SSSTik
    try:
        api2 = f"https://api.douyin.wtf/api?url={final_url}"
        r2 = requests.get(api2, headers=headers, timeout=10).json()
        if r2.get("nwm_video_url"):
            return r2.get("nwm_video_url")
    except Exception as e:
        logging.error(f"Backup API 1 Error: {e}")

    # Backup API 2: Loovik Emergency Server
    try:
        api3 = f"https://api.loovik.com/tiktok?url={final_url}"
        r3 = requests.get(api3, headers=headers, timeout=10).json()
        if r3.get("video"):
            return r3.get("video")
    except Exception as e:
        logging.error(f"Backup API 2 Error: {e}")

    return None

# --- 5. Channel Inline Buttons ---
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

# --- 6. Auto Post News to Channel ---
async def auto_post_news(context: ContextTypes.DEFAULT_TYPE):
    try:
        news_text = (
            "⚽ *تغطية إخبارية حصرية | DZ Football*\n\n"
            "🚨 *أبرز عناوين اليوم:*\n"
            "• متابعة مستمرة لأحدث الانتقالات وأخبار المحترفين.\n"
            "• تحضيرات مكثفة للأندية استعداداً للجولة القادمة.\n\n"
            "🔴 اشترك وشارك القناة لتصلك الأخبار فور حدوثها!"
        )
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=news_text,
            reply_markup=get_channel_buttons(),
            parse_mode='Markdown'
        )
    except Exception as e:
        logging.error(f"Error auto posting news: {e}")

# --- 7. Auto Post Standings to Channel ---
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
            "\n\n"
            "📌 يتم تحديث النتائج والتصنيفات بشكل دوري!"
        )
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=global_text,
            reply_markup=get_channel_buttons(),
            parse_mode='Markdown'
        )
    except Exception as e:
        logging.error(f"Error auto posting standings: {e}")

# --- 8. Private Messages & Video Downloader Handler ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "tiktok.com" in text:
        wait_msg = await update.message.reply_text("⏳ جاري استخراج الفيديو بجودة عالية HD بدون علامة مائية...")
        try:
            video_url = get_clean_tiktok_url(text)
            if video_url:
                await update.message.reply_video(
                    video=video_url,
                    caption="✅ *تم التحميل بأعلى جودة ممتازة عبر بوت DZ Football!*"
                )
            else:
                await update.message.reply_text("❌ تعذر تحميل الفيديو. تأكد من صحة الرابط وأن الحساب عام.")
        except Exception as e:
            logging.error(f"Handle message error: {e}")
            await update.message.reply_text("❌ حدث خطأ مؤقت في السيرفر، يرجى المحاولة بعد قليل.")
        finally:
            await wait_msg.delete()
    else:
        welcome_text = (
            "أهلاً بك في بوت *DZ Football* الشامل! ⚽🌍\n\n"
            "🔹 *في القناة:* ننشر تلقائياً الأخبار والتصنيفات العالمية.\n"
            "🔹 *في الخاص:* أرسل لي أي رابط من تيك توك لتحميله فوراً بأعلى جودة HD وبدون علامة مائية."
        )
        await update.message.reply_text(welcome_text, parse_mode='Markdown')

# --- 9. Main Bot Execution ---
if __name__ == '__main__':
    keep_alive()
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    job_queue = app.job_queue
    job_queue.run_repeating(auto_post_news, interval=3600, first=10)
    job_queue.run_repeating(auto_post_global_standings, interval=21600, first=60)

    app.run_polling(drop_pending_updates=True)
