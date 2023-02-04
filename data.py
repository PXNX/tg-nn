import inspect
import logging
from dataclasses import fields
from typing import Dict, List, Union, Optional

import psycopg2
from psycopg2.extras import NamedTupleCursor

from config import DATABASE_URL
from model import Account, Source, SourceDisplay

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


def get_sources_by_api_id(api_id: int) -> [Source]:
    try:
        with conn.cursor() as c:
            c.execute("select * from sources where api_id = %s", [api_id])
            res = c.fetchall()

            print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ", res)

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

            if hasattr(s,  'display_name') and s.display_name is not None:
                name = s.display_name
            else:
                name = s.channel_name

            if hasattr(s, 'bias') and s.bias is not None:
                bias = s.bias
            else:
                bias = ""

            return SourceDisplay(0, name, bias, s.username)

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
                if s.display_name is not None:
                    name = s.display_name
                else:
                    name = s.channel_name

                if s.bias is not None:
                    bias = s.bias
                else:
                    bias = ""

                res[s.channel_id] = SourceDisplay(0, name, bias, s.username)

            print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> RES: ", res)
            return res
    except Exception as e:
        logger.error(f"{inspect.currentframe().f_code.co_name} — DB-Operation failed", e)
        pass


def set_sources( sources: Dict[int, Dict[str, Union[str, int]]]):
    field_names = [field.name for field in fields(Source)]
    s_input = list()
    b_input = list()

    for k, v in sources.items():
        d = [ k]

        for f in field_names[1:]:
            if f in v:
                d.append(v[f])
            else:
                d.append(None)

        s_input.append(d)

        if "bloat" in v:
            for bloat in v["bloat"]:
                b_input.append([k,bloat])



    print("s_input",s_input)

    col = ",".join(field_names)

    row = "%s"
    for i in range(1, len(field_names)):
        row += ", %s"

    try:
        with conn.cursor() as c:
           c.executemany(f"INSERT INTO sources({col}) VALUES ({row})", s_input)
           c.executemany(f"INSERT INTO bloats(channel_id,pattern) VALUES (%s, '%s')", b_input)
           # sources = c.fetchall()
           conn.commit()

    except Exception as e:
        logger.error(f"{inspect.currentframe().f_code.co_name} — DB-Operation failed", e)
        pass




