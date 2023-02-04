import yaml
from pyrogram import Client

import account
from data import set_sources


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
    with open("sources.yaml", "rb") as stream:
        sources = yaml.safe_load(stream)
        print(sources)

        set_sources(sources)


append_sources()
