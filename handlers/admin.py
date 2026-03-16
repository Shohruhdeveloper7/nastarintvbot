import os
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.queries import (
    add_movie, delete_movie, get_movie_by_code, get_all_movies,
    add_channel, remove_channel, get_active_channels,
    get_statistics, get_top_movies, get_all_users,
    add_admin, remove_admin, get_all_admins, is_admin,
    block_user, unblock_user, get_user
)
from keyboards.keyboards import (
    admin_menu, main_menu, confirm_broadcast, confirm_delete_movie
)

router = Router()

SUPER_ADMIN_ID = int(os.getenv("SUPER_ADMIN_ID", "0"))


# ─── STATES ──────────────────────────────────────────────

class AddMovie(StatesGroup):
    code     = State()
    title    = State()
    title_uz = State()
    year     = State()
    genre    = State()
    desc     = State()
    video    = State()
    thumb    = State()


class AddChannel(StatesGroup):
    channel_id   = State()
    channel_name = State()
    channel_link = State()


class BroadcastState(StatesGroup):
    message = State()


class DeleteMovieState(StatesGroup):
    code = State()
    

class DeleteChannelState(StatesGroup):
    channel_id = State()


class ManageAdmin(StatesGroup):
    user_id = State()
    action  = State()


class BlockUser(StatesGroup):
    user_id = State()


# ─── ADMIN CHECK ─────────────────────────────────────────

async def admin_required(message: Message) -> bool:
    if not await is_admin(message.from_user.id) and message.from_user.id != SUPER_ADMIN_ID:
        await message.answer("⛔ Siz admin emassiz!")
        return False
    return True


# ─── ADMIN PANEL ─────────────────────────────────────────

@router.message(F.text == "👑 Admin panel")
async def admin_panel(message: Message):
    if not await admin_required(message):
        return
    await message.answer("👑 <b>Admin panel</b>", reply_markup=admin_menu(), parse_mode="HTML")


@router.message(F.text == "🏠 Asosiy menyu")
async def back_to_main(message: Message):
    await message.answer("🏠 Asosiy menyu", reply_markup=main_menu())


# ─── ADD MOVIE ───────────────────────────────────────────

@router.message(F.text == "➕ Kino qo'shish")
async def add_movie_start(message: Message, state: FSMContext):
    if not await admin_required(message):
        return
    await state.set_state(AddMovie.code)
    await message.answer(
        "🎬 <b>Kino qo'shish</b>\n\n"
        "1️⃣ Kino uchun <b>kod</b> kiriting (faqat raqam):\n"
        "<i>Misol: <code>101</code> yoki <code>2055</code></i>\n\n"
        "<i>Bekor qilish: /cancel</i>",
        parse_mode="HTML"
    )


@router.message(AddMovie.code)
async def add_movie_code(message: Message, state: FSMContext):
    code = message.text.strip()
    if not code.isdigit():
        await message.answer(
            "❌ Kod faqat <b>raqamlardan</b> iborat bo'lishi kerak!\nQayta kiriting:",
            parse_mode="HTML"
        )
        return
    existing = await get_movie_by_code(code)
    if existing:
        await message.answer(
            f"❌ <b>{code}</b> kodi allaqachon ishlatilgan!\n"
            f"({existing['title']} — ushbu kodda kino mavjud)\n\n"
            "Boshqa kod kiriting:",
            parse_mode="HTML"
        )
        return
    await state.update_data(code=code)
    await state.set_state(AddMovie.title)
    await message.answer("2️⃣ Kino nomini (inglizcha) yozing:", parse_mode="HTML")


@router.message(AddMovie.title)
async def add_movie_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(AddMovie.title_uz)
    await message.answer("3️⃣ O'zbekcha nomi (bo'lmasa — <code>-</code> yozing):", parse_mode="HTML")


@router.message(AddMovie.title_uz)
async def add_movie_title_uz(message: Message, state: FSMContext):
    val = message.text.strip()
    await state.update_data(title_uz=None if val == "-" else val)
    await state.set_state(AddMovie.year)
    await message.answer("4️⃣ Yili (masalan: <code>2023</code>, bo'lmasa — <code>-</code>):", parse_mode="HTML")


@router.message(AddMovie.year)
async def add_movie_year(message: Message, state: FSMContext):
    val = message.text.strip()
    year = None
    if val != "-":
        try:
            year = int(val)
        except ValueError:
            await message.answer("❌ Yil raqam bo'lishi kerak! Qayta kiriting:")
            return
    await state.update_data(year=year)
    await state.set_state(AddMovie.genre)
    await message.answer("5️⃣ Janri (masalan: <code>Drama, Komedia</code>, bo'lmasa — <code>-</code>):", parse_mode="HTML")


@router.message(AddMovie.genre)
async def add_movie_genre(message: Message, state: FSMContext):
    val = message.text.strip()
    await state.update_data(genre=None if val == "-" else val)
    await state.set_state(AddMovie.desc)
    await message.answer("6️⃣ Qisqa tavsif (bo'lmasa — <code>-</code>):", parse_mode="HTML")


@router.message(AddMovie.desc)
async def add_movie_desc(message: Message, state: FSMContext):
    val = message.text.strip()
    await state.update_data(desc=None if val == "-" else val)
    await state.set_state(AddMovie.video)
    await message.answer("7️⃣ Kino faylini yuboring (video):")


@router.message(AddMovie.video, F.video)
async def add_movie_video(message: Message, state: FSMContext):
    await state.update_data(file_id=message.video.file_id)
    await state.set_state(AddMovie.thumb)
    await message.answer(
        "8️⃣ Muqova rasmini yuboring (poster).\n"
        "Bo'lmasa — <code>-</code> yozing:",
        parse_mode="HTML"
    )


@router.message(AddMovie.thumb)
async def add_movie_thumb(message: Message, state: FSMContext):
    thumb_id = None
    if message.photo:
        thumb_id = message.photo[-1].file_id
    elif message.text and message.text.strip() == "-":
        thumb_id = None
    else:
        await message.answer("❌ Rasm yuboring yoki <code>-</code> yozing:", parse_mode="HTML")
        return

    data = await state.get_data()
    await state.clear()

    movie_id = await add_movie(
        code=data['code'],
        title=data['title'],
        title_uz=data.get('title_uz'),
        year=data.get('year'),
        genre=data.get('genre'),
        description=data.get('desc'),
        file_id=data['file_id'],
        thumbnail_id=thumb_id,
        added_by=message.from_user.id
    )

    await message.answer(
        f"✅ <b>Kino muvaffaqiyatli qo'shildi!</b>\n\n"
        f"🎬 Nomi: <b>{data['title']}</b>\n"
        f"🔢 <b>Kodi: {data['code']}</b>\n\n"
        f"Foydalanuvchilar <code>{data['code']}</code> kodini yuborsalar, shu kinoni olishadi!",
        parse_mode="HTML",
        reply_markup=admin_menu()
    )


@router.message(AddMovie.video)
async def add_movie_video_wrong(message: Message):
    await message.answer("❌ Video fayl yuboring!")


# ─── DELETE MOVIE ────────────────────────────────────────

@router.message(F.text == "🗑 Kino o'chirish")
async def delete_movie_start(message: Message, state: FSMContext):
    if not await admin_required(message):
        return
    await state.set_state(DeleteMovieState.code)
    await message.answer(
        "🗑 O'chirmoqchi bo'lgan kino kodini yozing:\n"
        "<i>Masalan: <code>1001</code></i>",
        parse_mode="HTML"
    )


@router.message(DeleteMovieState.code)
async def delete_movie_confirm(message: Message, state: FSMContext):
    code = message.text.strip()
    movie = await get_movie_by_code(code)
    if not movie:
        await message.answer(f"❌ <b>{code}</b> kodli kino topilmadi!", parse_mode="HTML")
        await state.clear()
        return

    await state.update_data(movie_id=movie['id'], movie_title=movie['title'])
    await message.answer(
        f"⚠️ <b>{movie['title']}</b> (kod: {code}) kinoni o'chirasizmi?",
        reply_markup=confirm_delete_movie(movie['id']),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("confirm_delete_"))
async def confirm_delete(callback: CallbackQuery, state: FSMContext):
    movie_id = int(callback.data.split("_")[2])
    await delete_movie(movie_id)
    await state.clear()
    await callback.message.edit_text("✅ Kino o'chirildi!")
    await callback.answer()


@router.callback_query(F.data == "cancel_delete")
async def cancel_delete(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Bekor qilindi.")
    await callback.answer()


# ─── CHANNELS ────────────────────────────────────────────

@router.message(F.text == "📢 Kanal qo'shish")
async def add_channel_start(message: Message, state: FSMContext):
    if not await admin_required(message):
        return
    await state.set_state(AddChannel.channel_id)
    await message.answer(
        "📢 <b>Kanal qo'shish</b>\n\n"
        "Kanal ID sini yozing (masalan: <code>@mening_kanalim</code> yoki <code>-1001234567890</code>):",
        parse_mode="HTML"
    )


@router.message(AddChannel.channel_id)
async def add_channel_id(message: Message, state: FSMContext):
    await state.update_data(channel_id=message.text.strip())
    await state.set_state(AddChannel.channel_name)
    await message.answer("Kanal nomini yozing (foydalanuvchiga ko'rsatiladigan nom):")


@router.message(AddChannel.channel_name)
async def add_channel_name(message: Message, state: FSMContext):
    await state.update_data(channel_name=message.text.strip())
    await state.set_state(AddChannel.channel_link)
    await message.answer("Kanal havolasini yozing (masolan: <code>https://t.me/kanal</code>):", parse_mode="HTML")


@router.message(AddChannel.channel_link)
async def add_channel_link(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    await add_channel(data['channel_id'], data['channel_name'], message.text.strip())
    await message.answer(
        f"✅ <b>{data['channel_name']}</b> kanali qo'shildi!\n"
        "Endi foydalanuvchilar bu kanalga obuna bo'lishlari kerak bo'ladi.",
        reply_markup=admin_menu(),
        parse_mode="HTML"
    )


@router.message(F.text == "❌ Kanal o'chirish")
async def remove_channel_handler(message: Message, state: FSMContext):
    if not await admin_required(message):
        return
    channels = await get_active_channels()
    if not channels:
        await message.answer("😔 Hozircha kanal yo'q.")
        return

    text = "📋 <b>Kanallar ro'yxati:</b>\n\n"
    for ch in channels:
        text += f"• <code>{ch['channel_id']}</code> — {ch['channel_name']}\n"
    text += "\nO'chirish uchun kanal ID sini yozing:"
    await state.set_state(DeleteChannelState.channel_id)
    await message.answer(text, parse_mode="HTML")


@router.message(DeleteChannelState.channel_id)
async def delete_channel_by_id(message: Message, state: FSMContext):
    channel_id = message.text.strip()
    await state.clear()
    await remove_channel(channel_id)
    await message.answer(
        f"✅ <code>{channel_id}</code> kanali o'chirildi!",
        reply_markup=admin_menu(),
        parse_mode="HTML"
    )


@router.message(F.text == "📋 Barcha kanallar")
async def list_channels(message: Message):
    if not await admin_required(message):
        return
    channels = await get_active_channels()
    if not channels:
        await message.answer("😔 Hozircha majburiy kanal yo'q.")
        return

    text = "📋 <b>Majburiy kanallar:</b>\n\n"
    for i, ch in enumerate(channels, 1):
        text += f"{i}. <b>{ch['channel_name']}</b>\n   ID: <code>{ch['channel_id']}</code>\n\n"
    await message.answer(text, parse_mode="HTML")


# ─── BROADCAST ───────────────────────────────────────────

@router.message(F.text == "📨 Reklama yuborish")
async def broadcast_start(message: Message, state: FSMContext):
    if not await admin_required(message):
        return
    await state.set_state(BroadcastState.message)
    await message.answer(
        "📨 <b>Reklama xabarini yozing:</b>\n\n"
        "Matn, rasm yoki video yuborishingiz mumkin.\n"
        "<i>Bekor qilish: /cancel</i>",
        parse_mode="HTML"
    )


@router.message(BroadcastState.message)
async def broadcast_preview(message: Message, state: FSMContext):
    await state.update_data(
        text=message.text,
        photo=message.photo[-1].file_id if message.photo else None,
        video=message.video.file_id if message.video else None,
        caption=message.caption
    )
    await message.answer(
        "👆 Yuqoridagi xabar barcha foydalanuvchilarga yuboriladi.\n\n"
        "Tasdiqlaysizmi?",
        reply_markup=confirm_broadcast()
    )


@router.callback_query(F.data == "confirm_broadcast")
async def do_broadcast(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()
    await callback.message.edit_text("📨 Yuborilmoqda...")

    users = await get_all_users()
    sent = 0
    failed = 0

    for user in users:
        try:
            if data.get('photo'):
                await bot.send_photo(user['id'], data['photo'], caption=data.get('caption', ''))
            elif data.get('video'):
                await bot.send_video(user['id'], data['video'], caption=data.get('caption', ''))
            elif data.get('text'):
                await bot.send_message(user['id'], data['text'])
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)  # Flood limitdan himoya

    await callback.message.answer(
        f"✅ <b>Reklama yuborildi!</b>\n\n"
        f"✅ Yuborildi: {sent}\n"
        f"❌ Xato: {failed}",
        parse_mode="HTML",
        reply_markup=admin_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "cancel_broadcast")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Reklama bekor qilindi.")
    await callback.answer()


# ─── STATISTICS ──────────────────────────────────────────

@router.message(F.text == "📊 Statistika")
async def statistics_handler(message: Message):
    if not await admin_required(message):
        return
    stats = await get_statistics()
    top = await get_top_movies(limit=3)

    text = (
        "📊 <b>Bot statistikasi</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{stats['total_users']}</b>\n"
        f"🆕 Bugun yangi: <b>{stats['today_users']}</b>\n"
        f"📅 Haftalik yangi: <b>{stats['weekly_users']}</b>\n"
        f"🟢 Bugun faol: <b>{stats['active_today']}</b>\n"
        f"🚫 Bloklangan: <b>{stats['blocked_users']}</b>\n\n"
        f"🎬 Jami kinolar: <b>{stats['total_movies']}</b>\n"
        f"👁 Jami ko'rishlar: <b>{stats['total_views']}</b>\n"
    )

    if top:
        text += "\n🏆 <b>Top 3 kino:</b>\n"
        for i, m in enumerate(top, 1):
            text += f"{i}. {m['title']} — 👁 {m['views']}\n"

    await message.answer(text, parse_mode="HTML")


# ─── ADMINS MANAGEMENT ───────────────────────────────────

@router.message(F.text == "👥 Adminlar")
async def admins_list(message: Message):
    if message.from_user.id != SUPER_ADMIN_ID:
        await message.answer("⛔ Faqat super admin!")
        return

    admins = await get_all_admins()
    text = "👥 <b>Adminlar ro'yxati:</b>\n\n"
    for a in admins:
        text += f"• ID: <code>{a['user_id']}</code>\n"

    text += (
        "\n➕ Admin qo'shish: <code>/addadmin USER_ID</code>\n"
        "➖ Admin o'chirish: <code>/removeadmin USER_ID</code>"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text.startswith("/addadmin"))
async def add_admin_cmd(message: Message):
    if message.from_user.id != SUPER_ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Ishlatish: <code>/addadmin USER_ID</code>", parse_mode="HTML")
        return
    try:
        uid = int(parts[1])
    except ValueError:
        await message.answer("❌ Noto'g'ri ID!")
        return
    await add_admin(uid, message.from_user.id)
    await message.answer(f"✅ <code>{uid}</code> admin qilindi!", parse_mode="HTML")


@router.message(F.text.startswith("/removeadmin"))
async def remove_admin_cmd(message: Message):
    if message.from_user.id != SUPER_ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Ishlatish: <code>/removeadmin USER_ID</code>", parse_mode="HTML")
        return
    try:
        uid = int(parts[1])
    except ValueError:
        await message.answer("❌ Noto'g'ri ID!")
        return
    await remove_admin(uid)
    await message.answer(f"✅ <code>{uid}</code> adminlikdan olindi!", parse_mode="HTML")


# ─── BLOCK / UNBLOCK ─────────────────────────────────────

@router.message(F.text.startswith("/block"))
async def block_user_cmd(message: Message):
    if not await admin_required(message):
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Ishlatish: <code>/block USER_ID</code>", parse_mode="HTML")
        return
    try:
        uid = int(parts[1])
    except ValueError:
        await message.answer("❌ Noto'g'ri ID!")
        return
    await block_user(uid)
    await message.answer(f"🚫 <code>{uid}</code> bloklandi!", parse_mode="HTML")


@router.message(F.text.startswith("/unblock"))
async def unblock_user_cmd(message: Message):
    if not await admin_required(message):
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Ishlatish: <code>/unblock USER_ID</code>", parse_mode="HTML")
        return
    try:
        uid = int(parts[1])
    except ValueError:
        await message.answer("❌ Noto'g'ri ID!")
        return
    await unblock_user(uid)
    await message.answer(f"✅ <code>{uid}</code> blokdan chiqarildi!", parse_mode="HTML")


# ─── CANCEL ──────────────────────────────────────────────

@router.message(F.text == "/cancel")
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu())
