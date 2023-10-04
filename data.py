import inspect
import logging
import sys
from dataclasses import fields, make_dataclass
from traceback import format_exc
from typing import Dict, Union

import psycopg2
from psycopg2 import OperationalError
from psycopg2.extras import NamedTupleCursor

from config import DATABASE_URL
from model import Account, Source, SourceDisplay, Post, Destination

conn = psycopg2.connect(DATABASE_URL, cursor_factory=NamedTupleCursor)


def print_psycopg2_exception(err):
    err_type, err_obj, traceback = sys.exc_info()

    # get the line number when exception occured
    #   line_num = traceback.tb_lineno

    #  print ("\npsycopg2 ERROR:", err, "on line number:", line_num)
    #    print ("psycopg2 traceback:", traceback, "-- type:", err_type)

    # psycopg2 extensions.Diagnostics object attribute
    logging.error(f"extensions.Diagnostics: {err.diag}", )
    logging.error(f"pgerror: {err.pgerror} -- pgcode: {err.pgcode}")


def get_source_ids_by_api_id(api_id: int) -> [int]:
    try:
        with conn.cursor() as c:
            c.execute("select channel_name,channel_id from sources where api_id = %s and is_active=TRUE;", [api_id])
            res: [Source] = c.fetchall()

            print(f">>>> get_source_ids_by_api_id: {res}")

            source: Source
            return [source.channel_id for source in res]
    except OperationalError as err:
        print_psycopg2_exception(err)
        conn.rollback()
    except Exception as e:
        logging.error(f"{inspect.currentframe().f_code.co_name} — DB-Operation failed {repr(e)} - {format_exc()}")

        pass


def get_patterns(channel_id: int) -> [str]:
    try:
        with conn.cursor() as c:
            c.execute("select pattern from bloats where channel_id = %s;", [channel_id])
            res: [str] = [r[0] for r in c.fetchall()]

            logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> get_patterns: {res}")

            return res
    except OperationalError as err:
        print_psycopg2_exception(err)
        conn.rollback()
    except Exception as e:
        logging.error(f"{inspect.currentframe().f_code.co_name} — DB-Operation failed {repr(e)} - {format_exc()}")
        pass


def get_source(channel_id: int) -> SourceDisplay:
    try:
        with conn.cursor() as c:
            c.execute("select * from sources where channel_id = %s;", [channel_id])

            s: Source = c.fetchone()

            logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> SOURCE: {s}")
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

    except Exception or OperationalError as err:
        print_psycopg2_exception(err)
        conn.rollback()
    except Exception as e:
        logging.error(f"{inspect.currentframe().f_code.co_name} — DB-Operation failed {repr(e)} - {format_exc()}")
        pass


def get_sources() -> dict[int, SourceDisplay]:
    try:
        with conn.cursor() as c:
            c.execute("select * from sources")
            sources = c.fetchall()

            logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> SOURCES: {sources}")

            res = dict()
            s: Source
            for s in sources:
                res[s.channel_id] = SourceDisplay(
                    s.display_name or s.channel_name,
                    s.bias,
                    s.invite,
                    s.username,
                    s.detail_id,
                    s.destination
                )

            logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> RES: {res}")
            return res
    except OperationalError as err:
        print_psycopg2_exception(err)
        conn.rollback()
    except Exception as e:
        logging.error(f"{inspect.currentframe().f_code.co_name} — DB-Operation failed {repr(e)} - {format_exc()}")
        pass


def get_footer(channel_id: int) -> str | None:
    try:
        with conn.cursor() as c:
            c.execute("select footer from destinations where channel_id = %s;", [channel_id])

            s = c.fetchone()

            logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> FOOTER: {s}")
            return s[0]

    except OperationalError as err:
        print_psycopg2_exception(err)
        conn.rollback()
    except Exception as e:
        logging.error(f"{inspect.currentframe().f_code.co_name} — DB-Operation failed {repr(e)} - {format_exc()}")
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

    logging.info(f"s_input", s_input)

    col = ",".join(field_names)

    row = "%s"
    for i in range(1, len(field_names)):
        row += ", %s"

    logging.info(f"--- col:", col)

    try:
        with conn.cursor() as c:
            c.executemany(f"INSERT INTO sources({col}) VALUES ({row});", s_input)
            c.executemany(f"INSERT INTO bloats(channel_id,pattern) VALUES (%s, %s);", b_input)
            # sources = c.fetchall()
            conn.commit()

    except OperationalError as err:
        print_psycopg2_exception(err)
        conn.rollback()
    except Exception as e:
        logging.error(f"{inspect.currentframe().f_code.co_name} — DB-Operation failed {repr(e)} - {format_exc()}")
        pass


def set_post(post: Post):
    try:
        # fixme: ON DUPLICATE KEY UPDATE might be better here. still, this function should not be called in the first place!
        with conn.cursor() as c:
            c.execute("""INSERT INTO posts(destination,message_id,source_channel_id,source_message_id,backup_id, 
             reply_id,message_text,file_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);""",
                      (
                          post.destination, post.message_id, post.source_channel_id, post.source_message_id,
                          post.backup_id,
                          post.reply_id, post.message_text, post.file_id))
            conn.commit()

    except Exception or OperationalError as err:
        print_psycopg2_exception(err)
        conn.rollback()
    except Exception as e:
        logging.error(f"{inspect.currentframe().f_code.co_name} — DB-Operation failed {repr(e)} - {format_exc()}")
        pass


def get_post(source_channel_id: int, source_message_id: int) -> Post:
    try:
        with conn.cursor() as c:
            c.execute("select * from posts where source_channel_id = %s and source_message_id = %s;",
                      (source_channel_id, source_message_id))
            s: Post = c.fetchone()

            logging.info(f">>>>>>>>>>>>>>>>>>>>>>>> get_post >>>>>>>>>>>>>>>>> POST: {s}", )

            return s

    except OperationalError as err:
        print_psycopg2_exception(err)
        conn.rollback()
    except Exception as e:
        logging.error(f"{inspect.currentframe().f_code.co_name} — DB-Operation failed {repr(e)} - {format_exc()}")
        pass


def set_destination(destination: Destination):
    try:
        with conn.cursor() as c:
            c.execute("""INSERT INTO destinations( channel_id, name, group_id  ) VALUES (%s, %s,%s)""",
                      (destination.channel_id, destination.name, destination.group_id))
            conn.commit()

    except OperationalError as err:
        print_psycopg2_exception(err)
        conn.rollback()
    except Exception as e:
        logging.error(f"{inspect.currentframe().f_code.co_name} — DB-Operation failed {repr(e)} - {format_exc()}")
        pass


def get_accounts() -> [Account]:
    try:
        with conn.cursor() as c:
            c.execute("select * from accounts;")
            res: [Account] = c.fetchall()

            logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> get_accounts: {res}", )

            return res
    except OperationalError as err:
        print_psycopg2_exception(err)
        conn.rollback()
    except Exception as e:
        logging.error(f"{inspect.currentframe().f_code.co_name} — DB-Operation failed {repr(e)} - {format_exc()}")
        pass
