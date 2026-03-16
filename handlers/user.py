from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from database.queries import (
    search_movies, get_movie_by_code, get_all_movies,
    get_top_movies, get_favorites, add_favorite, remove_favorite,
    update_last_active, get_movies_count
)
from keyboards.keyboards import movie_keyboard, movies_pagination

router = Router()

async def send_movie(message: Message, movie: dict, bot: Bot, user_id: int):
    favorites = await get_favorites(user_id)
    fav_ids = [f['id'] for f in favorites]
    is_fav = movie['id'] in fav_ids

    caption = (
        f"🎬 <b>{movie['title']}</b>"
        + (f" / {movie['title_uz']}" if movie['title_uz'] else "") + "\n"
        + (f"📅 Yil: {movie['year']}\n" if movie['year'] else "")
        + (f"🎭 Janr: {movie['genre']}\n" if movie['genre'] else "")
        + (f"\n📝 {movie['description']}\n" if movie['description'] else "")
        + f"\n👁 Ko'rishlar: {movie['views']}"
        + f"\n🔢 Kod: <code>{movie['code']}</code>"
    )

    keyboard = movie_keyboard(movie['id'], movie['code'], is_fav)

    if movie['thumbnail_id']:
        await message.answer_photo(
            photo=movie['thumbnail_id'],
            caption=caption,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await message.answer_video(
            video=movie['file_id'],
            caption=f"🎬 {movie['title']} | Kod: {movie['code']}"
        )
    else:
        await message.answer_video(
            video=movie['file_id'],
            caption=caption,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

async def send_movie_by_code(message: Message, bot: Bot, code: str):
    movie = await get_movie_by_code(code)
    if not movie:
        await message.answer("❌ Kino topilmadi.")
        return
    await update_last_active(message.from_user.id)
    await send_movie(message, movie, bot, message.from_user.id)


@router.message(F.text == "🔍 Kino qidirish")
async def search_prompt(message: Message):
    await message.answer(
        "🔍 Kino nomini yozing yoki <b>raqamli kodni</b> yuboring.\n\n"
        "Misol: <code>1001</code> yoki <code>Avengers</code>",
        parse_mode="HTML"
    )


@router.message(F.text == "🎬 Barcha kinolar")
async def all_movies(message: Message):
    movies = await get_all_movies(limit=20, offset=0)
    total = await get_movies_count()

    if not movies:
        await message.answer("😔 Hozircha kino yo'q.")
        return

    text = f"🎬 <b>Barcha kinolar</b> (jami: {total})\n\n"
    for m in movies:
        text += f"🔢 <code>{m['code']}</code> — <b>{m['title']}</b>"
        if m['year']:
            text += f" ({m['year']})"
        text += "\n"
    text += "\n📌 Kodini yuboring, kinoni oling!"

    markup = movies_pagination(movies, 0, total)
    await message.answer(text, parse_mode="HTML", reply_markup=markup)


@router.callback_query(F.data.startswith("movies_"))
async def movies_page(callback: CallbackQuery):
    offset = int(callback.data.split("_")[1])
    movies = await get_all_movies(limit=20, offset=offset)
    total = await get_movies_count()

    text = f"🎬 <b>Barcha kinolar</b> (jami: {total})\n\n"
    for m in movies:
        text += f"🔢 <code>{m['code']}</code> — <b>{m['title']}</b>"
        if m['year']:
            text += f" ({m['year']})"
        text += "\n"
    text += "\n📌 Kodini yuboring, kinoni oling!"

    markup = movies_pagination(movies, offset, total)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=markup)
    await callback.answer()


@router.message(F.text == "📊 Top kinolar")
async def top_movies(message: Message):
    movies = await get_top_movies(limit=10)
    if not movies:
        await message.answer("😔 Hozircha kino yo'q.")
        return

    text = "📊 <b>Top 10 kinolar</b>\n\n"
    for i, m in enumerate(movies, 1):
        text += f"{i}. 🔢 <code>{m['code']}</code> — <b>{m['title']}</b> — 👁 {m['views']}\n"
    text += "\n📌 Kodini yuboring, kinoni oling!"
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "❤️ Sevimlilar")
async def favorites_handler(message: Message):
    movies = await get_favorites(message.from_user.id)
    if not movies:
        await message.answer(
            "😔 Sevimlilar ro'yxatingiz bo'sh.\n\n"
            "Kino ko'rganingizda ❤️ tugmasini bosing."
        )
        return

    text = "❤️ <b>Sevimli kinolaringiz:</b>\n\n"
    for m in movies:
        text += f"🔢 <code>{m['code']}</code> — <b>{m['title']}</b>\n"
    text += "\n📌 Kodini yuboring, kinoni qayta oling!"
    await message.answer(text, parse_mode="HTML")


@router.callback_query(F.data.startswith("fav_"))
async def toggle_favorite(callback: CallbackQuery):
    movie_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    favorites = await get_favorites(user_id)
    fav_ids = [f['id'] for f in favorites]

    if movie_id in fav_ids:
        await remove_favorite(user_id, movie_id)
        await callback.answer("💔 Sevimlilardan olib tashlandi")
        is_fav = False
    else:
        await add_favorite(user_id, movie_id)
        await callback.answer("❤️ Sevimlilarga qo'shildi!")
        is_fav = True

    await callback.message.edit_reply_markup(
        reply_markup=movie_keyboard(movie_id, "", is_fav)
    )


@router.message(F.text & ~F.text.startswith("/"))
async def search_handler(message: Message, bot: Bot):
    query = message.text.strip()

    # Faqat raqam — to'g'ridan-to'g'ri kod sifatida
    if query.isdigit():
        movie = await get_movie_by_code(query)
        if movie:
            await update_last_active(message.from_user.id)
            await send_movie(message, movie, bot, message.from_user.id)
        else:
            await message.answer(
                f"❌ <b>{query}</b> kodli kino topilmadi.\n\n"
                "📋 <b>🎬 Barcha kinolar</b> tugmasidan ro'yxatni ko'ring.",
                parse_mode="HTML"
            )
        return

    # Matn bo'yicha qidirish
    movies = await search_movies(query)
    if not movies:
        await message.answer(
            f"😔 '<b>{query}</b>' bo'yicha hech narsa topilmadi.\n\n"
            "💡 <b>Maslahat:</b>\n"
            "• Kino kodini yuboring: <code>1001</code>\n"
            "• Boshqacha yozib ko'ring\n"
            "• <b>🎬 Barcha kinolar</b> dan qidiring",
            parse_mode="HTML"
        )
        return

    if len(movies) == 1:
        await update_last_active(message.from_user.id)
        await send_movie(message, movies[0], bot, message.from_user.id)
        return

    text = f"🔍 <b>'{query}'</b> bo'yicha {len(movies)} ta natija:\n\n"
    for m in movies:
        text += f"🔢 <code>{m['code']}</code> — <b>{m['title']}</b>"
        if m['year']:
            text += f" ({m['year']})"
        if m['genre']:
            text += f" | {m['genre']}"
        text += f" | 👁 {m['views']}\n"
    text += "\n📌 Kino kodini yuboring!"
    await message.answer(text, parse_mode="HTML")
