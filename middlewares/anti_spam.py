from aiogram import BaseMiddleware
from aiogram.types import Message
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Callable, Dict, Any, Awaitable


class AntiSpamMiddleware(BaseMiddleware):
    def __init__(self, limit: int = 3, window: int = 5):
        self.limit = limit  # max xabar soni
        self.window = window  # soniya
        self.user_messages: Dict[int, list] = defaultdict(list)

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if not hasattr(event, 'from_user') or not event.from_user:
            return await handler(event, data)

        user_id = event.from_user.id
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window)

        # Eski xabarlarni tozalash
        self.user_messages[user_id] = [
            t for t in self.user_messages[user_id] if t > window_start
        ]

        if len(self.user_messages[user_id]) >= self.limit:
            await event.answer("⚠️ Iltimos, biroz kuting. Juda tez xabar yubormoqdasiz!")
            return

        self.user_messages[user_id].append(now)
        return await handler(event, data)
