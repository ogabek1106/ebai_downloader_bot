# 📦 Section 1: Imports
import os
import asyncio
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
import yt_dlp
import re

# 🛡️ Section 2: Logging & Bot Token
BOT_TOKEN = os.environ.get("BOT_TOKEN")
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
        "👋 Welcome to EBAI Reels Downloader!\n\n"
        "Just send me an Instagram Reel link.\nI’ll download it and delete it after 60 seconds. 🔥"
    )

async def handle_reel_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not re.match(r'https?://(www\.)?instagram\.com/reel/', url):
        return

    try:
        filename = download_reel(url)
        video = open(filename, 'rb')
        sent_video = await update.message.reply_video(video=video)
        video.close()

        # Countdown message below video
        countdown_msg = await update.message.reply_text("⏳ 60s remaining...", reply_to_message_id=sent_video.message_id)

        # Countdown loop every 10 seconds
        for i in range(50, 0, -10):
            await asyncio.sleep(10)
            await countdown_msg.edit_text(f"⏳ {i}s remaining...")

        # Final message
        await asyncio.sleep(10)
        await countdown_msg.edit_text("✅ See you soon!")

        # Wait a bit, then clean up
        await asyncio.sleep(5)
        await sent_video.delete()
        await countdown_msg.delete()
        await update.message.delete()
        os.remove(filename)

    except Exception as e:
        logger.error(f"Download error: {e}")
        await update.message.reply_text("⚠️ Failed to download the reel. Try another link or make sure it’s public.")

# 🚀 Section 5: Start the Bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'instagram\.com/reel'), handle_reel_link))
    app.run_polling()
