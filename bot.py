import os
import random
import threading
import requests
import logging
import feedparser
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError

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

# --- 3. Bot & Channel Configuration ---
TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = "@DZFootballNews"

# قائمة روابط RSS للأخبار الرياضية
RSS_FEEDS = [
    # --- مصادر جزائرية ---
    "https://www.echoroukonline.com/sport/feed",       # الشروق الرياضي
    "https://www.elheddaf.com/rss",                   # الهداف الرياضية
    "https://www.elkhabar.com/rss/sports",            # الخبر الرياضي
    "https://www.aps.dz/sport/feed",                  # وكالة الأنباء الجزائرية - رياضة
    
    # --- مصادر عالمية وعربية سريعة ---
    "https://www.aljazeera.net/rss/sport",            # الجزيرة نت رياضة
    "https://www.skynewsarabian.com/rss/v1/endpoint/sport", # سكاي نيوز رياضة
    "https://arabic.rt.com/rss/sport/",               # روسيا اليوم رياضة
    "https://feeds.bbci.co.uk/arabic/rss.xml"          # بي بي سي عربي رياضة
]

# --- 4. TikTok Downloader (Stable Engine) ---
def get_clean_tiktok_url(tiktok_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }
    
    # محاولة جلب رابط الفيديو المباشر عبر TikWM بدون حظر
    try:
        api_url = f"https://www.tikwm.com/api/?url={tiktok_url}&hd=1"
        res = requests.get(api_url, headers=headers, timeout=12).json()
        if res.get("code") == 0 and "data" in res:
            return res["data"].get("hdplay") or res["data"].get("play")
    except Exception as e:
        logging.error(f"TikWM Error: {e}")

    # محرك احتياطي سريع (Cobalt API)
    try:
        cobalt_api = "https://co.wuk.sh/api/json"
        payload = {"url": tiktok_url}
        headers_cobalt = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        r = requests.post(cobalt_api, json=payload, headers=headers_cobalt, timeout=12).json()
        if r.get("url"):
            return r.get("url")
    except Exception as e:
        logging.error(f"Cobalt API Error: {e}")

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

# --- 6. Helper Function: Check Subscribtion ---
async def is_user_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except TelegramError as e:
        logging.error(f"Check membership error: {e}")
        return True  # في حالة حدوث خلل تقني يتم السماح للمستخدم لاستخدام البوت

# --- 7. Auto Post REAL News to Channel ---
async def auto_post_news(context: ContextTypes.DEFAULT_TYPE):
    shuffled_feeds = list(RSS_FEEDS)
    random.shuffle(shuffled_feeds)
    for feed_url in shuffled_feeds:
        try:
            feed = feedparser.parse(feed_url)
            if feed.entries:
                latest = feed.entries[0]
                title = latest.title
                link = latest.link
                
                news_text = (
                    f"⚽ *عاجل | تغطية إخبارية حصرية*\n\n"
                    f"🚨 *{title}*\n\n"
                    f"🔗 [اقرأ الخبر كاملاً من المصدر]({link})\n\n"
                    f"🔴 اشترك في القناة لتصلك أحدث الأخبار فور حدوثها!"
                )
                await context.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=news_text,
                    reply_markup=get_channel_buttons(),
                    parse_mode='Markdown'
                )
                break
        except Exception as e:
            logging.error(f"Error reading feed {feed_url}: {e}")

# --- 8. Private Messages & Force Subscribe Handler ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # فحص الاشتراك الإجباري
    subscribed = await is_user_subscribed(context.bot, user_id)
    if not subscribed:
        sub_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 اشترك في القناة الآن", url="https://t.me/DZFootballNews")]
        ])
        must_sub_text = (
            "⚠️ *تنبيه:* لاستخدام البوت وتحميل الفيديوهات مجاناً، يجب عليك الاشتراك في القناة الرسمية أولاً!\n\n"
            "👇 اشترك الآن ثم أرسل رابط الفيديو مجدداً:"
        )
        await update.message.reply_text(must_sub_text, reply_markup=sub_keyboard, parse_mode='Markdown')
        return

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
            "🔹 *في القناة:* ننشر تلقائياً آخر الأخبار الرياضية الحقيقية.\n"
            "🔹 *في الخاص:* أرسل لي أي رابط من تيك توك لتحميله فوراً بأعلى جودة HD وبدون علامة مائية."
        )
        await update.message.reply_text(welcome_text, parse_mode='Markdown')

# --- 9. Main Bot Execution ---
if __name__ == '__main__':
    keep_alive()
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    job_queue = app.job_queue
    job_queue.run_repeating(auto_post_news, interval=7200, first=10)

    app.run_polling(drop_pending_updates=True)
