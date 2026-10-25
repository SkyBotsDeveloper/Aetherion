"""Exercise actor authorization and shared assistant use without Telegram access."""

import ast
import asyncio
import runpy
import unittest
from datetime import datetime
from functools import wraps
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Awaitable, Callable
from unittest.mock import AsyncMock

from pyrogram import Client
from pyrogram.enums import ChatMemberStatus, ChatType
from pyrogram.errors import RPCError
from pyrogram.types import CallbackQuery, Chat, Message, User


ROOT = Path(__file__).resolve().parents[1]


def functions(path, **namespace):
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    nodes = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    for node in nodes:
        node.decorator_list = []
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)
    return namespace


class ActorAuthorizationTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = SimpleNamespace(get_chat_member=AsyncMock())
        self.actor = User(id=42, first_name="Member")
        self.message = Message(id=1, client=self.client,
            chat=Chat(id=-100123, type=ChatType.SUPERGROUP),
            from_user=User(id=999, first_name="Bot", is_bot=True))
        self.query = CallbackQuery(id="check", from_user=self.actor,
            chat_instance="test", message=self.message)
        self.checks = runpy.run_path(str(ROOT / "AETH/utils/admin_check.py"))

    async def test_member_cannot_inherit_bot_admin_or_owner_permissions(self):
        async def membership(chat_id, user_id):
            status = ChatMemberStatus.OWNER if user_id == 999 else ChatMemberStatus.MEMBER
            return SimpleNamespace(status=status)
        self.client.get_chat_member.side_effect = membership
        self.assertFalse(await self.checks["is_admin"](self.query))
        self.assertFalse(await self.checks["is_group_owner"](self.query))
        self.client.get_chat_member.assert_awaited_with(-100123, 42)

    async def test_owner_and_admin_are_distinguished(self):
        for status, admin, owner in (
            (ChatMemberStatus.MEMBER, False, False),
            (ChatMemberStatus.ADMINISTRATOR, True, False),
            (ChatMemberStatus.OWNER, True, True),
        ):
            with self.subTest(status=status):
                self.client.get_chat_member.return_value = SimpleNamespace(status=status)
                self.assertEqual(await self.checks["is_admin"](self.query), admin)
                self.assertEqual(await self.checks["is_group_owner"](self.query), owner)

    async def test_inline_callbacks_and_unavailable_members_fail_closed(self):
        self.query.message = None
        self.assertFalse(await self.checks["is_admin"](self.query))
        self.query.message = self.message
        self.client.get_chat_member.side_effect = RPCError()
        self.assertFalse(await self.checks["is_admin"](self.query))
        self.assertFalse(await self.checks["is_group_owner"](self.query))

    async def test_filters_check_clicker_instead_of_message_author(self):
        admin, owner = AsyncMock(return_value=False), AsyncMock(return_value=False)
        ns = functions("AETH/utils/admin_filters.py", Message=Message, CallbackQuery=CallbackQuery,
            SUDOERS={999}, OWNER_ID=999, is_admin=admin, is_group_owner=owner)
        self.assertFalse(ns["sudo_filter_func"](None, None, self.query))
        self.assertFalse(ns["bot_owner_filter_func"](None, None, self.query))
        await ns["admin_filter_func"](None, None, self.query)
        await ns["group_owner_filter_func"](None, None, self.query)
        admin.assert_awaited_once_with(self.query)
        owner.assert_awaited_once_with(self.query)

    async def test_group_owner_has_rights_without_explicit_privilege_flags(self):
        self.client.get_chat_member.return_value = SimpleNamespace(
            status=ChatMemberStatus.OWNER, privileges=None)
        ns = functions("AETH/plugins/Manager/grouphandler.py", Message=Message,
            app=self.client, ChatMemberStatus=ChatMemberStatus, ChatType=ChatType)
        self.assertTrue(await ns["has_permission"](42, -100123, "can_pin_messages"))


class PrivilegeDecoratorTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = SimpleNamespace(get_chat_member=AsyncMock())
        self.message = SimpleNamespace(from_user=SimpleNamespace(id=42),
            chat=SimpleNamespace(id=-100123, type=ChatType.SUPERGROUP, title="Group"),
            reply_text=AsyncMock())
        self.ns = functions("AETH/utils/decorator.py", wraps=wraps, Client=Client,
            Message=Message, ChatType=ChatType, ChatMemberStatus=ChatMemberStatus,
            Handler=Callable[..., Awaitable[Any]], SUDOERS=SimpleNamespace(user_ids={7}))
        self.handler = AsyncMock()

    async def test_regular_members_cannot_run_privileged_handler(self):
        self.client.get_chat_member.return_value = SimpleNamespace(status=ChatMemberStatus.MEMBER, privileges=None)
        wrapped = self.ns["_user_priv_required"]("can_restrict_members", "restrict users")(self.handler)
        await wrapped(self.client, self.message)
        self.handler.assert_not_awaited()
        self.message.reply_text.assert_awaited_once()

    async def test_owner_and_correctly_privileged_admin_can_run_handler(self):
        wrapped = self.ns["_user_priv_required"]("can_restrict_members", "restrict users")(self.handler)
        for status, privileges, expected in (
            (ChatMemberStatus.OWNER, None, True),
            (ChatMemberStatus.ADMINISTRATOR, SimpleNamespace(can_restrict_members=True), True),
            (ChatMemberStatus.ADMINISTRATOR, None, False),
        ):
            self.handler.reset_mock()
            self.client.get_chat_member.return_value = SimpleNamespace(status=status, privileges=privileges)
            await wrapped(self.client, self.message)
            self.assertEqual(self.handler.await_count, int(expected))

    async def test_admin_command_in_private_chat_returns_usage_without_membership_lookup(self):
        self.message.chat.type = ChatType.PRIVATE
        await self.ns["admin_required"]("can_restrict_members")(self.handler)(self.client, self.message)
        self.client.get_chat_member.assert_not_awaited()
        self.handler.assert_not_awaited()

    async def test_bot_permissions_use_authenticated_bot(self):
        self.client.get_chat_member.return_value = SimpleNamespace(
            status=ChatMemberStatus.ADMINISTRATOR, privileges=SimpleNamespace(can_delete_messages=True))
        await self.ns["_require_bot_priv"]("can_delete_messages", "delete messages")(self.handler)(self.client, self.message)
        self.client.get_chat_member.assert_awaited_once_with(-100123, "me")
        self.handler.assert_awaited_once()


class BotCheckTest(unittest.IsolatedAsyncioTestCase):
    async def test_bot_check_uses_running_assistant_without_disconnecting_playback(self):
        async def history(*args, **kwargs):
            yield SimpleNamespace(from_user=SimpleNamespace(id=91))
        assistant = SimpleNamespace(is_connected=True, start=AsyncMock(), stop=AsyncMock(),
            get_users=AsyncMock(return_value=SimpleNamespace(id=91, mention="Test bot")),
            send_message=AsyncMock(), get_chat_history=history)
        idle = SimpleNamespace(is_connected=False)
        bots = SimpleNamespace(one=idle, two=assistant, three=idle, four=idle, five=idle)
        photo = SimpleNamespace(edit_caption=AsyncMock())
        msg = SimpleNamespace(from_user=SimpleNamespace(id=73265606),
            reply_text=AsyncMock(), reply_photo=AsyncMock(return_value=photo))
        ns = functions("AETH/plugins/sudo/botschk.py", userbot=bots, assistants=[2], OWNER_ID=73265606,
            BOT_LIST=["test_bot"], datetime=datetime, asyncio=SimpleNamespace(sleep=AsyncMock()))
        await ns["check_bots_command"](None, msg)
        assistant.send_message.assert_awaited_once_with(91, "/start")
        assistant.start.assert_not_awaited()
        assistant.stop.assert_not_awaited()
        photo.edit_caption.assert_awaited_once()


class CleanupConfirmationTest(unittest.IsolatedAsyncioTestCase):
    async def test_zombie_cleanup_rejects_cross_chat_callback_before_authorization(self):
        authorize = AsyncMock(return_value=True)
        ns = functions("AETH/plugins/Manager/zombie.py", Client=Client, CallbackQuery=CallbackQuery,
            Message=Message, List=list, is_admin=authorize, chatQueue=set(), stopProcess=False)
        query = SimpleNamespace(data="confirm_zombies:-100999",
            message=SimpleNamespace(chat=SimpleNamespace(id=-100123)), answer=AsyncMock())
        await ns["execute_zombie_cleanup"](None, query)
        authorize.assert_not_awaited()
        query.answer.assert_awaited_once_with("Invalid chat for this request.", show_alert=True)


if __name__ == "__main__":
    unittest.main()
