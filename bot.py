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
        "Just send me an Instagram Reel link. I’ll download it and delete it after 60 seconds. 🔥"
    )

async def handle_reel_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    # Basic check to make sure it's an Instagram reel
    if not re.match(r'https?://(www\.)?instagram\.com/reel/', url):
        return

    try:
        filename = download_reel(url)
        video = open(filename, 'rb')
        sent_msg = await update.message.reply_video(
            video=video,
            caption="📥 Here is your Reel! Auto-deletes in 60 seconds."
        )
        await asyncio.sleep(60)
        await sent_msg.delete()
        await update.message.delete()
        video.close()
        os.remove(filename)
    except Exception as e:
        logger.error(f"Download error: {e}")
        await update.message.reply_text("⚠️ Failed to download the reel. Try another link or make sure it’s public.")

# 🚀 Section 5: Run the Bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'instagram\.com/reel'), handle_reel_link))
    app.run_polling()
