import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

_pool = None


async def get_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(os.getenv("DATABASE_URL"))
    return _pool


async def init_db():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id BIGINT PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                joined_at TIMESTAMP DEFAULT NOW(),
                is_blocked BOOLEAN DEFAULT FALSE,
                last_active TIMESTAMP DEFAULT NOW(),
                total_requests INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS movies (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                title_uz TEXT,
                year INTEGER,
                genre TEXT,
                description TEXT,
                file_id TEXT NOT NULL,
                thumbnail_id TEXT,
                views INTEGER DEFAULT 0,
                added_by BIGINT,
                added_at TIMESTAMP DEFAULT NOW(),
                is_active BOOLEAN DEFAULT TRUE,
                code TEXT UNIQUE NOT NULL
            );

            CREATE TABLE IF NOT EXISTS channels (
                id SERIAL PRIMARY KEY,
                channel_id TEXT NOT NULL UNIQUE,
                channel_name TEXT NOT NULL,
                channel_link TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE
            );

            CREATE TABLE IF NOT EXISTS favorites (
                user_id BIGINT,
                movie_id INTEGER,
                added_at TIMESTAMP DEFAULT NOW(),
                PRIMARY KEY (user_id, movie_id)
            );

            CREATE TABLE IF NOT EXISTS broadcasts (
                id SERIAL PRIMARY KEY,
                message TEXT,
                sent_by BIGINT,
                sent_at TIMESTAMP DEFAULT NOW(),
                total_sent INTEGER DEFAULT 0,
                total_failed INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS admins (
                user_id BIGINT PRIMARY KEY,
                added_at TIMESTAMP DEFAULT NOW(),
                added_by BIGINT
            );

            CREATE TABLE IF NOT EXISTS statistics (
                id SERIAL PRIMARY KEY,
                date DATE DEFAULT CURRENT_DATE UNIQUE,
                new_users INTEGER DEFAULT 0,
                total_requests INTEGER DEFAULT 0,
                unique_active INTEGER DEFAULT 0
            );

            CREATE INDEX IF NOT EXISTS idx_movies_title ON movies USING gin(to_tsvector('simple', title));
            CREATE INDEX IF NOT EXISTS idx_movies_code ON movies(code);
            CREATE INDEX IF NOT EXISTS idx_users_joined ON users(joined_at);
        """)
