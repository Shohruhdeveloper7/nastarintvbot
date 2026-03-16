from database.db import get_pool


# ─── USERS ───────────────────────────────────────────────

async def add_user(user_id: int, username: str, full_name: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        is_new = await conn.fetchval(
            "SELECT COUNT(*) FROM users WHERE id = $1", user_id
        )
        await conn.execute("""
            INSERT INTO users (id, username, full_name)
            VALUES ($1, $2, $3)
            ON CONFLICT (id) DO UPDATE
            SET username = $2, full_name = $3, last_active = NOW()
        """, user_id, username, full_name)
        if not is_new:
            await conn.execute("""
                INSERT INTO statistics (date, new_users)
                VALUES (CURRENT_DATE, 1)
                ON CONFLICT (date) DO UPDATE
                SET new_users = statistics.new_users + 1
            """)


async def get_user(user_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)


async def update_last_active(user_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE users 
            SET last_active = NOW(), total_requests = total_requests + 1
            WHERE id = $1
        """, user_id)


async def get_all_users():
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("SELECT id FROM users WHERE is_blocked = FALSE")


async def block_user(user_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET is_blocked = TRUE WHERE id = $1", user_id)


async def unblock_user(user_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET is_blocked = FALSE WHERE id = $1", user_id)


async def get_users_count():
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval("SELECT COUNT(*) FROM users")


async def get_active_users_today():
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval("""
            SELECT COUNT(*) FROM users
            WHERE last_active::date = CURRENT_DATE
        """)


# ─── MOVIES ──────────────────────────────────────────────

async def get_next_movie_code() -> str:
    """Avtomatik raqamli kod — 1001 dan boshlab"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        last = await conn.fetchval(
            "SELECT MAX(CAST(code AS INTEGER)) FROM movies WHERE code ~ '^[0-9]+$'"
        )
        return str((last or 1000) + 1)


async def add_movie(code, title, title_uz, year, genre, description, file_id, thumbnail_id, added_by):
    pool = await get_pool()
    async with pool.acquire() as conn:
        movie_id = await conn.fetchval("""
            INSERT INTO movies 
            (title, title_uz, year, genre, description, file_id, thumbnail_id, added_by, code)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id
        """, title, title_uz, year, genre, description, file_id, thumbnail_id, added_by, code)
        return movie_id


async def get_movie_by_code(code: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        movie = await conn.fetchrow("""
            SELECT * FROM movies WHERE code = $1 AND is_active = TRUE
        """, code)
        if movie:
            await conn.execute(
                "UPDATE movies SET views = views + 1 WHERE code = $1", code
            )
        return movie


async def search_movies(query: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("""
            SELECT * FROM movies
            WHERE (
                title ILIKE $1
                OR title_uz ILIKE $1
                OR genre ILIKE $1
                OR CAST(year AS TEXT) = $2
            ) AND is_active = TRUE
            ORDER BY views DESC
            LIMIT 10
        """, f"%{query}%", query)


async def get_all_movies(limit=20, offset=0):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("""
            SELECT * FROM movies WHERE is_active = TRUE
            ORDER BY CAST(code AS INTEGER) DESC
            LIMIT $1 OFFSET $2
        """, limit, offset)


async def delete_movie(movie_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM movies WHERE id = $1", movie_id
        )


async def get_movies_count():
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval(
            "SELECT COUNT(*) FROM movies WHERE is_active = TRUE"
        )


async def get_top_movies(limit=10):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("""
            SELECT * FROM movies WHERE is_active = TRUE
            ORDER BY views DESC LIMIT $1
        """, limit)


# ─── CHANNELS ────────────────────────────────────────────

async def add_channel(channel_id, channel_name, channel_link):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO channels (channel_id, channel_name, channel_link)
            VALUES ($1, $2, $3)
            ON CONFLICT (channel_id) DO UPDATE
            SET channel_name = $2, channel_link = $3, is_active = TRUE
        """, channel_id, channel_name, channel_link)


async def get_active_channels():
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(
            "SELECT * FROM channels WHERE is_active = TRUE"
        )


async def remove_channel(channel_id: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE channels SET is_active = FALSE WHERE channel_id = $1", channel_id
        )


# ─── FAVORITES ───────────────────────────────────────────

async def add_favorite(user_id: int, movie_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        try:
            await conn.execute(
                "INSERT INTO favorites (user_id, movie_id) VALUES ($1, $2)",
                user_id, movie_id
            )
            return True
        except Exception:
            return False


async def remove_favorite(user_id: int, movie_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM favorites WHERE user_id = $1 AND movie_id = $2",
            user_id, movie_id
        )


async def get_favorites(user_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("""
            SELECT m.* FROM movies m
            JOIN favorites f ON m.id = f.movie_id
            WHERE f.user_id = $1 AND m.is_active = TRUE
            ORDER BY f.added_at DESC
        """, user_id)


# ─── ADMINS ──────────────────────────────────────────────

async def add_admin(user_id: int, added_by: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO admins (user_id, added_by) VALUES ($1, $2)
            ON CONFLICT DO NOTHING
        """, user_id, added_by)


async def remove_admin(user_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM admins WHERE user_id = $1", user_id)


async def is_admin(user_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM admins WHERE user_id = $1", user_id
        )
        return count > 0


async def get_all_admins():
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("SELECT * FROM admins")


# ─── STATISTICS ──────────────────────────────────────────

async def get_statistics():
    pool = await get_pool()
    async with pool.acquire() as conn:
        total_users   = await conn.fetchval("SELECT COUNT(*) FROM users")
        total_movies  = await conn.fetchval("SELECT COUNT(*) FROM movies WHERE is_active = TRUE")
        today_users   = await conn.fetchval("SELECT COUNT(*) FROM users WHERE joined_at::date = CURRENT_DATE")
        active_today  = await conn.fetchval("SELECT COUNT(*) FROM users WHERE last_active::date = CURRENT_DATE")
        total_views   = await conn.fetchval("SELECT COALESCE(SUM(views), 0) FROM movies")
        weekly_users  = await conn.fetchval("SELECT COUNT(*) FROM users WHERE joined_at >= NOW() - INTERVAL '7 days'")
        blocked_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_blocked = TRUE")
        return {
            "total_users":   total_users,
            "total_movies":  total_movies,
            "today_users":   today_users,
            "active_today":  active_today,
            "total_views":   total_views,
            "weekly_users":  weekly_users,
            "blocked_users": blocked_users,
        }
