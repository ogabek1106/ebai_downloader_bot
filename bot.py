# 📦 Section 1: Imports
import os
import re
import asyncio
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
import yt_dlp

# 🛡️ Section 2: Config
BOT_TOKEN = os.environ.get("BOT_TOKEN")
STORAGE_CHANNEL_ID = -1002580997752  # Your private channel ID

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 📥 Section 3: Reel Download Function
def download_reel(url):
    ydl_opts = {
        'format': 'mp4',
        'outtmpl': 'reel.%(ext)s',
        'quiet': True,
        'noplaylist': True,
        'cookiefile': 'ig_cookies.txt'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# 🤖 Section 4: Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Welcome to EBAI Reels Downloader!*\n\n"
        "*Just send me an Instagram Reel link. I’ll send it to you*\n\n"
        "⚠️ _We do not store or save downloaded content. All sent content will be auto-deleted from the chat after 60 seconds._ 🔥\n\n"
        "Any questions? Contact 👉 @Ogabek1106",
        parse_mode="Markdown"
    )

async def handle_reel_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not re.match(r'https?://(www\.)?instagram\.com/reel/', url):
        return

    try:
        filename = download_reel(url)
        video = open(filename, 'rb')

        # 1️⃣ Send to user
        sent_video = await update.message.reply_video(video=video)

        # 2️⃣ Send to storage channel with caption
        video.seek(0)
        user = update.effective_user
        name = f"@{user.username}" if user.username else f"{user.full_name} (ID: {user.id})"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        caption = f"📅 {timestamp}\n👤 {name}"
        await context.bot.send_video(chat_id=STORAGE_CHANNEL_ID, video=video, caption=caption)
        video.close()

        # ⏳ Countdown message
        countdown_msg = await update.message.reply_text("⏳ 60s remaining...", reply_to_message_id=sent_video.message_id)
        for i in range(50, 0, -10):
            await asyncio.sleep(10)
            await countdown_msg.edit_text(f"⏳ {i}s remaining...")
        await asyncio.sleep(10)
        await countdown_msg.edit_text("✅ See you soon!")

        # 🧹 Cleanup
        await asyncio.sleep(5)
        await sent_video.delete()
        await countdown_msg.delete()
        await update.message.delete()
        os.remove(filename)

    except Exception as e:
        logger.error(f"Download error: {e}")
        await update.message.reply_text("⚠️ Failed to download the reel. Try another link or make sure it’s public.")

# 🚀 Section 5: Start Bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'instagram\.com/reel'), handle_reel_link))
    app.run_polling()
