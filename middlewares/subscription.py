from aiogram import BaseMiddleware, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from typing import Callable, Dict, Any, Awaitable
from database.queries import get_active_channels


def fix_link(link: str) -> str:
    if link.startswith('http'):
        return link
    return f"https://t.me/{link.lstrip('@')}"


class SubscriptionMiddleware(BaseMiddleware):
    def __init__(self, bot: Bot):
        self.bot = bot

    async def check_subscription(self, user_id: int) -> tuple[bool, list]:
        channels = await get_active_channels()
        not_subscribed = []
        for channel in channels:
            try:
                member = await self.bot.get_chat_member(channel['channel_id'], user_id)
                if member.status in ('left', 'kicked', 'banned'):
                    not_subscribed.append(channel)
            except Exception:
                not_subscribed.append(channel)
        return len(not_subscribed) == 0, not_subscribed

    async def send_subscription_message(self, send_func, channels: list):
        buttons = []
        for ch in channels:
            buttons.append([
                InlineKeyboardButton(
                    text=f"📢 {ch['channel_name']}",
                    url=fix_link(ch['channel_link'])
                )
            ])
        buttons.append([
            InlineKeyboardButton(text="✅ Obuna bo'ldim", callback_data="check_subscription")
        ])
        markup = InlineKeyboardMarkup(inline_keyboard=buttons)
        await send_func(
            "🎬 <b>KinoBot</b>ga xush kelibsiz!\n\n"
            "Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:\n\n"
            "Obuna bo'lgach <b>✅ Obuna bo'ldim</b> tugmasini bosing.",
            reply_markup=markup,
            parse_mode="HTML"
        )

    async def __call__(
        self,
        handler: Callable,
        event: Any,
        data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, Message):
            user_id = event.from_user.id
            send_func = event.answer
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            send_func = event.message.answer
        else:
            return await handler(event, data)

        # Admin uchun obuna shart emas
        from database.queries import is_admin
        import os
        SUPER_ADMIN_ID = int(os.getenv("SUPER_ADMIN_ID", "0"))
        if user_id == SUPER_ADMIN_ID or await is_admin(user_id):
            return await handler(event, data)

        # check_subscription callback ni o'tkazib yuborish
        if isinstance(event, CallbackQuery) and event.data == "check_subscription":
            return await handler(event, data)

        # Barcha xabarlar uchun obuna tekshirish
        is_subscribed, not_subscribed = await self.check_subscription(user_id)
        if not is_subscribed:
            await self.send_subscription_message(send_func, not_subscribed)
            return

        return await handler(event, data)