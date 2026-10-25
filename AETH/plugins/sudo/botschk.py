import asyncio
from datetime import datetime
from pyrogram import filters
from AETH import app, userbot
from AETH.core.userbot import assistants
from config import OWNER_ID

BOT_LIST = [
    "Bloody_musicbot",
    "Aetherionmusicclubbot",
    "you_tubemusic2bot",
    "The_RaHa_BoT",
    "SkyBeatzBot"
]

@app.on_message(filters.command("botschk") & filters.group)
async def check_bots_command(client, message):
    if not message.from_user or message.from_user.id != OWNER_ID:
        return await message.reply_text("🚫 You are not authorized to use this command.")

    clients = (userbot.one, userbot.two, userbot.three, userbot.four, userbot.five)
    assistant = next(
        (clients[index - 1] for index in assistants if clients[index - 1].is_connected),
        None,
    )
    if assistant is None:
        return await message.reply_text("No assistant is connected. Try again after startup.")

    processing_msg = await message.reply_photo(
        photo="https://graph.org/file/e6b215db83839e8edf831.jpg",
        caption="**ᴄʜᴇᴄᴋɪɴɢ ʙᴏᴛs sᴛᴀᴛs ᴀʟɪᴠᴇ ᴏʀ ᴅᴇᴀᴅ...**"
    )

    start_time = datetime.now()

    response = "**ʙᴏᴛs sᴛᴀᴛᴜs ᴅᴇᴀᴅ ᴏʀ ᴀʟɪᴠᴇ ᴄʜᴇᴄᴋᴇʀ**\n\n"

    for bot_username in BOT_LIST:
        try:
            bot = await assistant.get_users(bot_username)
            await asyncio.sleep(0.5)
            await assistant.send_message(bot.id, "/start")
            await asyncio.sleep(3)
            
            async for bot_message in assistant.get_chat_history(bot.id, limit=1):
                status = "ᴏɴʟɪɴᴇ ✨" if bot_message.from_user and bot_message.from_user.id == bot.id else "ᴏғғʟɪɴᴇ ❄"
                response += f"╭⎋ {bot.mention}\n╰⊚ **sᴛᴀᴛᴜs: {status}**\n\n"
        except Exception:
            response += f"╭⎋ {bot_username}\n╰⊚ **sᴛᴀᴛᴜs: ᴇʀʀᴏʀ ❌**\n\n"
    
    last_checked_time = start_time.strftime("%Y-%m-%d")
    await processing_msg.edit_caption(f"{response}⏲️ ʟᴀsᴛ ᴄʜᴇᴄᴋ: {last_checked_time}")
