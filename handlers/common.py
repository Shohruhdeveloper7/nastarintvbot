from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from database.queries import add_user, get_active_channels, is_admin
from keyboards.keyboards import main_menu, admin_menu, check_subscription_keyboard
import os
router = Router()


async def check_user_subscription(bot: Bot, user_id: int) -> tuple[bool, list]:
    channels = await get_active_channels()
    not_subscribed = []
    for channel in channels:
        try:
            member = await bot.get_chat_member(channel['channel_id'], user_id)
            if member.status in ('left', 'kicked', 'banned'):
                not_subscribed.append(channel)
        except Exception:
            not_subscribed.append(channel)
    return len(not_subscribed) == 0, not_subscribed


@router.message(CommandStart())
async def start_handler(message: Message, bot: Bot):
    user = message.from_user
    await add_user(user.id, user.username or "", user.full_name or "")

    # Majburiy obuna tekshirish
    is_subscribed, not_subscribed = await check_user_subscription(bot, user.id)

    if not is_subscribed:
        await message.answer(
            f"👋 Salom, <b>{user.full_name}</b>!\n\n"
            "🎬 <b>KinoBot</b>ga xush kelibsiz!\n\n"
            "Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:",
            reply_markup=check_subscription_keyboard(not_subscribed),
            parse_mode="HTML"
        )
        return

    # Kino kodi bilan kelsa
    args = message.text.split()
    if len(args) > 1:
        from handlers.user import send_movie_by_code
        await send_movie_by_code(message, bot, args[1])
        return

    SUPER_ADMIN_ID = int(os.getenv("SUPER_ADMIN_ID", "0"))
    admin_check = await is_admin(user.id) or user.id == SUPER_ADMIN_ID
    keyboard = admin_menu() if admin_check else main_menu()

    await message.answer(
        f"👋 Salom, <b>{user.full_name}</b>!\n\n"
        "🎬 <b>KinoBot</b>ga xush kelibsiz!\n"
        "Qidirish uchun kino nomini yozing yoki menyudan tanlang.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery, bot: Bot):
    user = callback.from_user
    is_subscribed, not_subscribed = await check_user_subscription(bot, user.id)

    if not is_subscribed:
        await callback.answer("❌ Hali ham barcha kanallarga obuna bo'lmadingiz!", show_alert=True)
        return  # xabarni o'zgartirmaymiz

    await callback.message.delete()
    admin_check = await is_admin(user.id)
    SUPER_ADMIN_ID = int(os.getenv("SUPER_ADMIN_ID", "0"))
    keyboard = admin_menu() if (admin_check or user.id == SUPER_ADMIN_ID) else main_menu()

    await callback.message.answer(
        "✅ Rahmat! Endi botdan to'liq foydalanishingiz mumkin.\n\n"
        "🎬 Kino qidirish uchun kino kodini yuboring.",
        reply_markup=keyboard
    )
    await callback.answer()


@router.message(F.text == "ℹ️ Yordam")
async def help_handler(message: Message):
    await message.answer(
        "🎬 <b>KinoBot — Yordam</b>\n\n"
        "📌 <b>Qanday ishlatiladi?</b>\n"
        "• Kino nomini yozing — bot topib beradi\n"
        "• Yoki kod orqali: /start <code>KOD</code>\n\n"
        "📌 <b>Funksiyalar:</b>\n"
        "🔍 Kino qidirish — nom, yil, janr bo'yicha\n"
        "❤️ Sevimlilar — yoqtirgan kinolaringiz\n"
        "📊 Top kinolar — eng ko'p ko'rilganlar\n\n"
        "📌 <b>Muammo bo'lsa:</b>\n"
        "• 📞 Aloqa tugmasini bosing",
        parse_mode="HTML"
    )


@router.message(F.text == "📞 Aloqa")
async def contact_handler(message: Message):
    await message.answer(
        "📞 <b>Aloqa</b>\n\n"
        "Admin: @your_admin_username\n"
        "Taklif va shikoyatlar uchun yozing.",
        parse_mode="HTML"
    )
