from pyrogram.types import CallbackQuery
from pyrogram.enums import ChatType, ChatMemberStatus
from pyrogram.errors import RPCError

async def is_admin(message_or_cq) -> bool:
    if isinstance(message_or_cq, CallbackQuery):
        message = message_or_cq.message
        actor = message_or_cq.from_user
    else:
        message = message_or_cq
        actor = message.from_user

    if not message or not actor:
        return False

    if message.chat.type not in [ChatType.SUPERGROUP, ChatType.CHANNEL, ChatType.GROUP]:
        return False

    client = message._client
    try:
        member = await client.get_chat_member(message.chat.id, actor.id)
    except RPCError:
        return False
    return member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]

async def is_group_owner(message_or_cq) -> bool:
    if isinstance(message_or_cq, CallbackQuery):
        message = message_or_cq.message
        actor = message_or_cq.from_user
    else:
        message = message_or_cq
        actor = message.from_user

    if not message or not actor:
        return False

    if message.chat.type not in [ChatType.SUPERGROUP, ChatType.CHANNEL, ChatType.GROUP]:
        return False

    client = message._client
    try:
        member = await client.get_chat_member(message.chat.id, actor.id)
    except RPCError:
        return False
    return member.status == ChatMemberStatus.OWNER
