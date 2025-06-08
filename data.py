import logging
from dataclasses import fields
from functools import wraps
from typing import Dict, Union, List

from psycopg2 import OperationalError, connect
from psycopg2.extras import NamedTupleCursor

from config import DATABASE_URL
from model import Account, Source, SourceDisplay, Post, Destination

conn = connect(DATABASE_URL, cursor_factory=NamedTupleCursor)


def db_operation(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            with conn.cursor() as cursor:
                result = func(cursor, *args, **kwargs)
                conn.commit()
                logging.info(f"{func.__name__} RESULT: {result}")
                return result
        except (OperationalError, Exception) as e:
            logging.error(f"{func.__name__} failed: {e}")
            conn.rollback()

    return wrapper


@db_operation
def get_source_ids_by_api_id(c, api_id: int) -> List[int]:
    c.execute("select channel_name,channel_id from sources where api_id = %s and is_active=TRUE;", [api_id])
    res: List[Source] = c.fetchall()
    source: Source
    return [source.channel_id for source in res]


@db_operation
def get_patterns(c, channel_id: int) ->List [str]:
    c.execute("select pattern from bloats where channel_id = %s;", [channel_id])
    res: List[str] = [r[0] for r in c.fetchall()]
    return res


@db_operation
def get_source(c, channel_id: int) -> SourceDisplay:
    c.execute("select * from sources where channel_id = %s;", [channel_id])

    s: Source = c.fetchone()
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


@db_operation
def get_sources(c) -> dict[int, SourceDisplay]:
    c.execute("select * from sources")
    sources = c.fetchall()
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


@db_operation
def get_footer(c, channel_id: int) -> str | None:
    c.execute("select footer from destinations where channel_id = %s;", [channel_id])
    s = c.fetchone()
    return s[0]


@db_operation
def set_sources(c, sources: Dict[int, Dict[str, Union[str, int]]]):
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

    c.executemany(f"INSERT INTO sources({col}) VALUES ({row});", s_input)
    c.executemany(
        "INSERT INTO bloats(channel_id,pattern) VALUES (%s, %s);", b_input
    )


@db_operation
def set_post(c, post: Post):
    c.execute("""INSERT INTO posts(destination,message_id,source_channel_id,source_message_id,backup_id, 
             reply_id,message_text,file_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);""",
              (
                  post.destination, post.message_id, post.source_channel_id, post.source_message_id,
                  post.backup_id,
                  post.reply_id, post.message_text, post.file_id))


@db_operation
def get_post(c, source_channel_id: int, source_message_id: int) -> Post:
    c.execute("select * from posts where source_channel_id = %s and source_message_id = %s;",
              (source_channel_id, source_message_id))
    s: Post = c.fetchone()
    return s


@db_operation
def set_destination(c, destination: Destination):
    c.execute("""INSERT INTO destinations( channel_id, name, group_id  ) VALUES (%s, %s,%s)""",
              (destination.channel_id, destination.name, destination.group_id))


@db_operation
def get_accounts(c) -> List[Account]:
    c.execute("select * from accounts;")
    res:List [Account] = c.fetchall()
    return res
