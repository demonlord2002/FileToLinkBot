from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from pymongo import MongoClient
from config import *
import os, uuid, asyncio, uvicorn

# --------------------------
#  FastAPI Web Server Setup
# --------------------------
app = FastAPI()

@app.get("/")
async def home():
    return {"status": "online", "message": "File To Link Bot is working!"}

@app.get("/dl/{file_id}")
async def download(file_id: str):
    data = collection.find_one({"_id": file_id})
    if not data:
        return {"error": "File not found"}
    return RedirectResponse(url=data["file_url"])

@app.get("/watch/{file_id}")
async def watch(file_id: str):
    data = collection.find_one({"_id": file_id})
    if not data:
        return {"error": "File not found"}
    file_url = data["file_url"]
    html = f"""
    <html>
    <head><title>{data['file_name']}</title></head>
    <body style='text-align:center;'>
        <video width='90%' height='auto' controls autoplay>
            <source src='{file_url}' type='video/mp4'>
        </video>
        <p><a href='{file_url}' download>Download File</a></p>
    </body></html>
    """
    return html

# --------------------------
#  MongoDB Connection
# --------------------------
mongo = MongoClient(DATABASE_URL)
db = mongo["filetolink_db"]
collection = db["files"]

# --------------------------
#  Telegram Bot Setup
# --------------------------
bot = Client("FileToLinkBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.private & filters.media)
async def handle_file(client, message):
    try:
        # Check 2 GB limit
        if message.document and message.document.file_size > 2_000_000_000:
            return await message.reply_text("⚠️ Sorry! Telegram bots can only handle files up to 2 GB.")

        file = await message.copy(chat_id=BIN_CHANNEL)
        file_id = str(uuid.uuid4())
        file_url = f"https://t.me/{file.chat.username}/{file.id}" if file.chat.username else file.link

        collection.insert_one({
            "_id": file_id,
            "file_name": message.document.file_name if message.document else "Media",
            "file_url": file_url
        })

        base = FQDN.rstrip("/")
        dl_link = f"{base}/dl/{file_id}"
        watch_link = f"{base}/watch/{file_id}"
        share_link = f"https://t.me/{client.me.username}?start=file_{file_id}"

        buttons = [
            [InlineKeyboardButton("📥 Download", url=dl_link)],
            [InlineKeyboardButton("🎬 Watch Online", url=watch_link)],
            [InlineKeyboardButton("🔗 Share", url=share_link)]
        ]

        await message.reply_text(
            f"**✅ Your Link Generated!**\n\n📂 File Name: `{message.document.file_name if message.document else 'Media'}`\n\n📥 [Download]({dl_link})\n🖥 [Watch]({watch_link})",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    except Exception as e:
        await message.reply_text(f"⚠️ Oops! Error: {e}")

# --------------------------
#  Start Bot and Web Server (Heroku Fix)
# --------------------------
import threading

def run_web():
    uvicorn.run(app, host="0.0.0.0", port=PORT)

def run_bot():
    bot.run()  # handles long polling internally

if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    run_bot()
