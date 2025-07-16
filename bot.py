# 📦 Section 1: Imports
import os
import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import yt_dlp

# 🛡️ Section 2: Config & Logging
BOT_TOKEN = os.environ.get("BOT_TOKEN")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 📥 Section 3: Reel Downloader
def download_reel(url):
    ydl_opts = {
        'format': 'mp4',
        'outtmpl': 'reel.%(ext)s',
        'quiet': True,
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# 🤖 Section 4: Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Send /reel <Instagram Reel URL> to download a video.\n\nVideo will auto-delete in 1 minute.")

async def reel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗️Please provide an Instagram Reel URL.")
        return

    url = context.args[0]
    try:
        filename = download_reel(url)
        sent = await update.message.reply_video(video=open(filename, 'rb'), caption="📥 Downloaded Reel (Auto-deletes in 60s)")
        await asyncio.sleep(60)
        await sent.delete()
        await update.message.delete()
        os.remove(filename)
    except Exception as e:
        logger.error(f"Error downloading: {e}")
        await update.message.reply_text("⚠️ Failed to download the reel. Try another link or make sure it’s public.")

# 🚀 Section 5: Start the Bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reel", reel))
    app.run_polling()
