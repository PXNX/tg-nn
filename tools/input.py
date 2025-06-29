import yaml
from pyrogram import Client

from bot.db import set_sources, set_destination, get_accounts
from bot.model import Destination


async def extract_chats():
    # todo:shit
    for a in get_accounts():
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

        for k, v in content.items():
            print(k, v)
            set_destination(Destination(k, v["name"], v["group_id"] if "group_id" in v else None))
            for k2, v2 in v["sources"].items():
                print(k2, v2)
                v2["destination"] = k
            print("----------------------")
            print(v["sources"])
            set_sources(v["sources"])


append_sources()
