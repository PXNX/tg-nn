import logging
import sys
from contextlib import asynccontextmanager
from dataclasses import fields
from functools import wraps
from os import getenv
from ssl import create_default_context, Purpose, CERT_NONE
from typing import Dict, Union, List, Optional, Callable, Awaitable, Any

from asyncpg import Pool, create_pool, Connection, Record

from bot.config import DATABASE_URL
from bot.model import Account, Source, SourceDisplay, Post, Destination


def record_to_dataclass(record: Record, dataclass_type) -> Any:
    """Convert asyncpg Record to dataclass"""
    field_names = [f.name for f in fields(dataclass_type)]
    values = {name: record[name] for name in field_names if name in record}
    return dataclass_type(**values)


def get_ssl():
    ssl_ctx = create_default_context(Purpose.SERVER_AUTH)
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = CERT_NONE
    return ssl_ctx


class DBPool:
    _pool: Optional[Pool] = None

    @classmethod
    def is_test(cls) -> bool:
        return 'pytest' in sys.modules or getenv('TESTING') == 'true'

    @classmethod
    async def get_pool(cls) -> Optional[Pool]:
        if cls.is_test():
            return None
        if cls._pool is None:
            cls._pool = await create_pool(DATABASE_URL)
        return cls._pool

    @classmethod
    @asynccontextmanager
    async def connection(cls):
        if cls.is_test():
            yield None
            return

        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            yield conn


def db(func: Callable[..., Awaitable]):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        async with DBPool.connection() as conn:
            if DBPool.is_test():
                return await func(*args, **kwargs)
            kwargs["conn"] = conn
            return await func(*args, **kwargs)

    return wrapper


@db
async def get_source_ids_by_api_id(api_id: int, conn: Connection) -> List[int]:
    res: List[Record] = await conn.fetch(
        "select channel_name,channel_id from sources where api_id =  $1 and is_active=TRUE;", [api_id])
    return [source["channel_id"] for source in res]


@db
async def get_patterns(channel_id: int, conn: Connection) -> List[str]:
    s = await conn.fetch("select pattern from bloats where channel_id = $1;", [channel_id])
    res: List[str] = [r[0] for r in s]
    return res


@db
async def get_source(channel_id: int, conn: Connection) -> SourceDisplay:
    s: Source = await conn.fetchrow("select * from sources where channel_id = $1;", [channel_id])

    sd = SourceDisplay(
        display_name=s.display_name or s.channel_name,
        bias=s.bias,
        invite=s.invite,
        username=s.username,
        detail_id=s.detail_id,
        destination=s.destination
    )

    logging.info(f"sd >>>>>>>>>> {sd}")
    return sd


@db
async def get_sources(conn: Connection) -> dict[int, SourceDisplay]:
    sources = await conn.fetch("select * from sources", [])
    s: Source
    return {
        s.channel_id: SourceDisplay(
            s.display_name or s.channel_name,
            s.bias,
            s.invite,
            s.username,
            s.detail_id,
            s.destination,
        )
        for s in sources
    }


@db
async def get_footer(channel_id: int, conn: Connection) -> str | None:
    s = await conn.fetchval("select footer from destinations where channel_id =  $1;", [channel_id])
    return s


@db
async def set_sources(sources: Dict[int, Dict[str, Union[str, int]]], conn: Connection):
    field_names = [field.name for field in fields(Source)]
    s_input = []
    b_input = []

    for k, v in sources.items():
        d = [k]

        for f in field_names[1:]:
            if f in v:
                d.append(v[f])
            else:
                d.append(None)

        s_input.append(d)

        if "bloat" in v:
            b_input.extend([k, bloat] for bloat in v["bloat"])
    logging.info("s_input", s_input)

    col = ",".join(field_names)

    row = "%s"
    for _ in range(1, len(field_names)):
        row += ", %s"

    logging.info("--- col:", col)

    await conn.executemany(f"INSERT INTO sources({col}) VALUES ({row});", s_input)
    await conn.executemany(
        "INSERT INTO bloats(channel_id,pattern) VALUES ( $1,  $2);", b_input
    )


@db
async def set_post(post: Post, conn: Connection):
    await conn.execute("""INSERT INTO posts(destination,message_id,source_channel_id,source_message_id,backup_id, 
             reply_id,message_text,file_id) VALUES ($1, $2, $3,$4, $5, $6,$7, $8 );""",
                       (
                           post.destination, post.message_id, post.source_channel_id, post.source_message_id,
                           post.backup_id,
                           post.reply_id, post.message_text, post.file_id))


@db
async def get_post(source_channel_id: int, source_message_id: int, conn: Connection) -> Post:
    s: Post = await conn.fetchrow("select * from posts where source_channel_id =  $1 and source_message_id =  $2;",
                                  [source_channel_id, source_message_id])
    return s


@db
async def set_destination(destination: Destination, conn: Connection):
    await conn.execute("INSERT INTO destinations( channel_id, name, group_id  ) VALUES ( $1, $2, $3)",
                       (destination.channel_id, destination.name, destination.group_id))


@db
async def get_accounts(conn: Connection) -> List[Account]:
    records: List[Record] = await conn.fetch("select * from accounts;", )
    accs = [record_to_dataclass(r, Account) for r in records]
    return accs
