from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import API_ID, API_HASH, BOT_TOKEN, BIN_CHANNEL, FQDN
from pymongo import MongoClient
import os, uuid

mongo = MongoClient(os.getenv("DATABASE_URL"))
db = mongo["filetolink"]
files = db["files"]

bot = Client("FileToLinkBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.private & filters.media)
async def save_file(client, message):
    sent = await message.forward(BIN_CHANNEL)
    file_id = str(uuid.uuid4())
    file_name = message.document.file_name if message.document else "file"
    file_size = message.document.file_size if message.document else 0

    files.insert_one({
        "_id": file_id,
        "file_id": sent.id,
        "file_name": file_name,
        "file_size": file_size
    })

    dl_link = f"{FQDN}/dl/{file_id}"
    watch_link = f"{FQDN}/watch/{file_id}"
    share_link = f"https://t.me/{client.me.username}?start=file_{file_id}"

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Download", url=dl_link)],
        [InlineKeyboardButton("🖥 Watch", url=watch_link)],
        [InlineKeyboardButton("🔗 Share", url=share_link)]
    ])

    caption = f"""**𝗬𝗼𝘂𝗿 𝗟𝗶𝗻𝗸 𝗚𝗲𝗻𝗲𝗿𝗮𝘁𝗲𝗱 !**

📂 **File Name:** {file_name}
📦 **Size:** {round(file_size/1024/1024, 2)} MB

📥 **Download:** {dl_link}
🖥 **Watch:** {watch_link}
🔗 **Share:** {share_link}
"""
    await message.reply_text(caption, reply_markup=buttons)

bot.run()
