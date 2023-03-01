import inspect
import logging
from dataclasses import fields
from re import Pattern
from typing import Dict, Union

import psycopg2
from psycopg2.extras import NamedTupleCursor

from config import DATABASE_URL
from model import Account, Source, SourceDisplay, Post, Destination

logger = logging.getLogger(__name__)

conn = psycopg2.connect(DATABASE_URL, cursor_factory=NamedTupleCursor)


def get_accounts() -> [Account]:
    try:
        with conn.cursor() as c:
            c.execute("select * from accounts")
            res = c.fetchall()

            print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ", res)

            return res
    except Exception as e:
        logger.error(f"{inspect.currentframe().f_code.co_name} — DB-Operation failed", e)
        pass


def get_source_ids_by_api_id(api_id: int) -> [int]:
    try:
        with conn.cursor() as c:
            c.execute("select channel_name,channel_id from sources where api_id = %s", [api_id])
            res: [Source] = c.fetchall()

            print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ", res)

            source: Source
            return [source.channel_id for source in res]
    except Exception as e:
        logger.error(f"{inspect.currentframe().f_code.co_name} — DB-Operation failed", e)
        pass


def get_patterns(channel_id: int) -> [Pattern]:
    try:
        with conn.cursor() as c:
            c.execute("select pattern from bloats where channel_id = %s", [channel_id])
            res = c.fetchall()

            print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> get_ptterns: ", res)

            return res
    except Exception as e:
        logger.error(f"{inspect.currentframe().f_code.co_name} — DB-Operation failed", e)
        pass


def get_source(channel_id: int) -> SourceDisplay:
    try:
        with conn.cursor() as c:
            c.execute("select * from sources where channel_id = %s", [channel_id])
            s: Source = c.fetchone()

            print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> SOURCE: ", s)

            if hasattr(s, 'display_name') and s.display_name is not None:
                name = s.display_name
            else:
                name = s.channel_name

            if hasattr(s, 'bias') and s.bias is not None:
                bias = s.bias
            else:
                bias = ""

            if hasattr(s, 'detail_id') and s.detail_id is not None:
                detail = s.detail_id
            else:
                detail = None

            return SourceDisplay(detail, name, bias, s.username,s.destination or 703453307)

    except Exception as e:
        logger.error(f"{inspect.currentframe().f_code.co_name} — DB-Operation failed", e)
        pass


def get_sources() -> dict[int, SourceDisplay]:
    try:
        with conn.cursor() as c:
            c.execute("select * from sources")
            sources = c.fetchall()

            print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> SOURCES: ", sources)

            res = dict()
            s: Source
            for s in sources:
                res[s.channel_id] = SourceDisplay(0,
                                                  s.display_name or s.channel_name,
                                                  s.bias or "",
                                                  s.username,
                                                  s.destination
                                                  )

            print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> RES: ", res)
            return res
    except Exception as e:
        logger.error(f"{inspect.currentframe().f_code.co_name} — DB-Operation failed", e)
        pass


def set_sources(sources: Dict[int, Dict[str, Union[str, int]]]):
    field_names = [field.name for field in fields(Source)]
    s_input = list()
    b_input = list()

    for k, v in sources.items():
        d = [k]

        for f in field_names[1:]:
            if f in v:
                d.append(v[f])
            else:
                d.append(None)

        s_input.append(d)

        if "bloat" in v:
            for bloat in v["bloat"]:
                b_input.append([k, bloat])

    print("s_input", s_input)

    col = ",".join(field_names)

    row = "%s"
    for i in range(1, len(field_names)):
        row += ", %s"

    try:
        with conn.cursor() as c:
            c.executemany(f"INSERT INTO sources({col}) VALUES ({row})  ", s_input)
            c.executemany(f"INSERT INTO bloats(channel_id,pattern) VALUES (%s, %s)", b_input)
            # sources = c.fetchall()
            conn.commit()

    except Exception as e:
        logger.error(f"{inspect.currentframe().f_code.co_name} — DB-Operation failed", e)
        pass


def set_post(post: Post):
    try:
        with conn.cursor() as c:
            c.execute("""INSERT INTO posts( channel_id, message_id, source_channel_id, source_message_id, backup_id, 
             reply_id,  message_text,  file_id ) VALUES (%s, %s,%s,%s,%s,%s,'%s',%s)""",
                      (post.channel_id, post.message_id, post.source_channel_id, post.source_message_id, post.backup_id,
                       post.reply_id, post.message_text, post.file_id))
            conn.commit()

    except Exception as e:
        logger.error(f"{inspect.currentframe().f_code.co_name} — DB-Operation failed", e)
        pass


def get_post(channel_id: int, message_id: int) -> Post:
    try:
        with conn.cursor() as c:
            c.execute("select * from posts where channel_id = %s and message_id = %s", (channel_id, message_id))
            s: Post = c.fetchone()

            print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> SOURCE: ", s)

            return s

    except Exception as e:
        logger.error(f"{inspect.currentframe().f_code.co_name} — DB-Operation failed", e)
        pass

def set_destination(destination: Destination):
    try:
        with conn.cursor() as c:
            c.execute("""INSERT INTO destinations( channel_id, name, group_id  ) VALUES (%s, %s,%s)""",
                      (destination.channel_id,destination.name, destination.group_id))
            conn.commit()

    except Exception as e:
        logger.error(f"{inspect.currentframe().f_code.co_name} — DB-Operation failed", e)
        pass