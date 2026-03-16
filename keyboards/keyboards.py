from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)


# ─── USER KEYBOARDS ──────────────────────────────────────

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Kino qidirish"), KeyboardButton(text="🎬 Barcha kinolar")],
            [KeyboardButton(text="❤️ Sevimlilar"), KeyboardButton(text="📊 Top kinolar")],
            [KeyboardButton(text="ℹ️ Yordam"), KeyboardButton(text="📞 Aloqa")],
        ],
        resize_keyboard=True
    )


def movie_keyboard(movie_id: int, movie_code: str, is_favorite: bool = False):
    fav_text = "💔 Sevimlilardan o'chirish" if is_favorite else "❤️ Sevimlilarga qo'shish"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=fav_text, callback_data=f"fav_{movie_id}")],
        [InlineKeyboardButton(text="📤 Ulashish", switch_inline_query=f"kino_{movie_code}")],
    ])


def movies_pagination(movies, offset, total):
    buttons = []
    nav = []
    if offset > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"movies_{offset - 20}"))
    if offset + 20 < total:
        nav.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"movies_{offset + 20}"))
    if nav:
        buttons.append(nav)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def check_subscription_keyboard(channels: list):
    buttons = []
    for ch in channels:
        link = ch['channel_link']
        if not link.startswith('http'):
            link = f"https://t.me/{link.lstrip('@')}"
        buttons.append([InlineKeyboardButton(text=f"📢 {ch['channel_name']}", url=link)])
    buttons.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subscription")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ─── ADMIN KEYBOARDS ─────────────────────────────────────

def admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Kino qo'shish"), KeyboardButton(text="🗑 Kino o'chirish")],
            [KeyboardButton(text="📢 Kanal qo'shish"), KeyboardButton(text="❌ Kanal o'chirish")],
            [KeyboardButton(text="📨 Reklama yuborish"), KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="👥 Adminlar"), KeyboardButton(text="📋 Barcha kanallar")],
            [KeyboardButton(text="🏠 Asosiy menyu")],
        ],
        resize_keyboard=True
    )


def confirm_broadcast():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha, yuborish", callback_data="confirm_broadcast"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_broadcast"),
        ]
    ])


def confirm_delete_movie(movie_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ O'chirish", callback_data=f"confirm_delete_{movie_id}"),
            InlineKeyboardButton(text="❌ Bekor", callback_data="cancel_delete"),
        ]
    ])
