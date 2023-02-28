import yaml
from pyrogram import Client

import account
from data import set_sources, set_destination
from model import Destination


async def extract_chats():
    # todo:shit
    for a in account.accounts:
        print(f"Account {a.name} >>>>>")
        app = Client(
            name=a.name,
            api_id=a.api_id,
            api_hash=a.api_hash,
            phone_number=a.phone_number,
            #   phone_code=input(f"phone code {a.name}:"),
            password="area"
        )

        d = dict()
        async for chat in app.get_dialogs():
            print(app.name, chat)

            d += {
                "channel_id"
            }


def append_sources():
    with open("import.yaml", "rb") as stream:
        content = yaml.safe_load(stream)

        for k,v in content.items():
            print(k,v)
            set_destination(Destination(k, v["name"], v["group_id"] if "group_id" in v else None))
            set_sources(v["sources"])


append_sources()
