# 📦 Section 1: Imports
import os
import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import yt_dlp

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

# 🤖 Section 4: Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to EBAI Reels Downloader Bot!\n\n"
        "Send me a Reel using:\n"
        "`/reel <Instagram URL>`\n\n"
        "📌 The video will be deleted in 60 seconds for your privacy.",
        parse_mode="Markdown"
    )

async def reel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗️Please provide an Instagram Reel URL.")
        return

    url = context.args[0]
    try:
        filename = download_reel(url)
        video = open(filename, 'rb')
        sent_msg = await update.message.reply_video(video=video, caption="📥 Here is your Reel! Auto-deletes in 60 seconds.")
        await asyncio.sleep(60)
        await sent_msg.delete()
        await update.message.delete()
        video.close()
        os.remove(filename)
    except Exception as e:
        logger.error(f"Download error: {e}")
        await update.message.reply_text("⚠️ Failed to download the reel. Try another link or make sure it's public.")

# 🚀 Section 5: Start the Bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reel", reel))
    app.run_polling()
