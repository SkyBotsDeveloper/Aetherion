from pyrogram import filters
from pyrogram.types import Message

from AETH import app
from AETH.core.call import JARVIS
from AETH.utils.database import is_music_playing, music_off
from AETH.utils.decorators import AdminRightsCheck
from AETH.utils.inline import close_markup
from config import BANNED_USERS
from AETH.utils.rich_buttons import rich_call


@app.on_message(filters.command(["pause", "cpause"]) & filters.group & ~BANNED_USERS)
@AdminRightsCheck
async def pause_admin(cli, message: Message, _, chat_id):
    if not await is_music_playing(chat_id):
        return await message.reply_text(_["admin_1"])
    await music_off(chat_id)
    await JARVIS.pause_stream(chat_id)
    await rich_call(message.reply_text,
        _["admin_2"].format(message.from_user.mention), reply_markup=close_markup(_)
    )
