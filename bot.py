# 📦 Section 1: Imports
import os
import re
import json
import time
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
STORAGE_CHANNEL_ID = -1002580997752
USER_FILE = "user_ids.json"
COOKIE_STRING = "75749405793%3AW4A7dwxoZ4dURE%3A9%3AAYehidp6fTBSowEZYh8ssY6XPVIigXMqNtmILwky6A"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 📊 Section 3: User Tracker
def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            return json.load(f)
    return []

def save_users(user_ids):
    with open(USER_FILE, "w") as f:
        json.dump(user_ids, f)

user_ids = load_users()

# 📥 Section 4: Reel Downloader
def download_reel(url):
    def try_download(fmt):
        unique_name = f"reel_{int(time.time()*1000)}"
        ydl_opts = {
            'format': fmt,
            'outtmpl': f'{unique_name}.%(ext)s',
            'quiet': True,
            'noplaylist': True,
            'cookiesfrombrowser': ('chrome',),
            'cookiefile': 'ig_cookies.txt'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if not os.path.exists(filename):
                raise Exception("❌ File not saved after download.")
            return filename, info

    base_formats = ['mp4[height<=720]', 'mp4[height<=480]', 'best']
    wide_format = 'bestvideo[ext=mp4][width>=720]+bestaudio/best[ext=mp4][width>=720]'

    for fmt in base_formats:
        try:
            filename, info = try_download(fmt)
            size_mb = os.path.getsize(filename) / 1024 / 1024
            if info.get("width") and info.get("height"):
                ratio = info["width"] / info["height"]
                if ratio < 0.8:
                    try:
                        os.remove(filename)
                        filename, info = try_download(wide_format)
                    except Exception as e:
                        logger.warning(f"Wide format fallback failed: {e}")

            return filename, info
        except Exception as e:
            logger.warning(f"Download failed for format {fmt}: {e}")
            continue

    raise Exception("❌ No suitable format found or video > 50MB")

# 🤖 Section 5: Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Welcome to EBAI Reels Downloader!*\n\n"
        "*Just send me an Instagram Reel link. I’ll send it to you*\n\n"
        "⚠️ _We do not store or save downloaded content. All sent content will be auto-deleted from the chat after 60 seconds._ 🔥\n\n"
        "Any questions? Contact 👉 @Ogabek1106",
        parse_mode="Markdown"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"👥 Total users: {len(user_ids)}")

async def handle_reel_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not re.match(r'https?://(www\.)?instagram\.com/reel/', url):
        return

    user = update.effective_user
    user_id = user.id

    if user_id not in user_ids:
        user_ids.append(user_id)
        save_users(user_ids)

    # 👨🏻‍💻 Notify user
    downloading_msg = await update.message.reply_text("Downloading...👨🏻‍💻")

    try:
        filename, info = download_reel(url)

        if not os.path.exists(filename):
            raise Exception("❌ File not found after download.")

        size_mb = os.path.getsize(filename) / 1024 / 1024
        video = open(filename, 'rb')

        name = f"@{user.username}" if user.username else f"{user.full_name} (ID: {user.id})"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        caption = f"📅 {timestamp}\n👤 {name}"

        # Send to private storage channel
        storage_msg = await context.bot.send_video(
            chat_id=STORAGE_CHANNEL_ID,
            video=video,
            caption=caption
        )

        video.seek(0)

        if size_mb <= 49:
            sent_video = await update.message.reply_video(video=video)
            video.close()

            async def countdown_and_cleanup():
                try:
                    countdown_msg = await update.message.reply_text("⏳ 60s remaining...", reply_to_message_id=sent_video.message_id)
                    for i in range(50, 0, -10):
                        await asyncio.sleep(10)
                        await countdown_msg.edit_text(f"⏳ {i}s remaining...")
                    await asyncio.sleep(10)
                    await countdown_msg.edit_text("✅ See you soon!")
                    await asyncio.sleep(5)
                    await sent_video.delete()
                    await countdown_msg.delete()
                    await update.message.delete()
                    os.remove(filename)
                except Exception as e:
                    logger.error(f"Cleanup error: {e}")

            context.application.create_task(countdown_and_cleanup())

        else:
            video.close()
            message_link = f"https://t.me/c/{str(STORAGE_CHANNEL_ID)[4:]}/{storage_msg.message_id}"
            too_big_msg = await update.message.reply_text(
                f"⚠️ The video is too large to send here.\n\n📥 Download it here 👉 [View Reel]({message_link})",
                parse_mode="Markdown",
                disable_web_page_preview=True
            )

            async def auto_delete():
                await asyncio.sleep(180)
                await too_big_msg.delete()
                await update.message.delete()
                os.remove(filename)

            context.application.create_task(auto_delete())

    except Exception as e:
        logger.error(f"Download error: {e}")
        await update.message.reply_text(
            f"⚠️ Failed to download the reel.\n\nError: `{str(e)}`",
            parse_mode="Markdown"
        )
    finally:
        await downloading_msg.delete()

# 🚀 Section 6: Run Bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'instagram\.com/reel'), handle_reel_link))
    app.run_polling()
