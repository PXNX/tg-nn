import dataclasses
import logging
from typing import Optional, List

import yaml

import psycopg2
from psycopg2.extras import NamedTupleCursor

from config import DB_URL


logger = logging.getLogger(__name__)
conn = psycopg2.connect(DB_URL, cursor_factory=NamedTupleCursor)

def get_sources(user_id:int) -> [Post]:
    try:
        with conn.cursor() as c:
            c.execute("select * from posts p where p.media_group_id = %s and p.lang='de'", [meg_id])
            res = c.fetchall()

            print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ", res)

            return res
    except Exception as e:
        logger.error("DB-Operation failed", e)
        pass

sources = dict()
