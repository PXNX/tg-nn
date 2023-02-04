from datetime import datetime, timedelta
from time import timezone

from pyrogram import Client, idle, filters
from pyrogram.enums import ParseMode
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

import account
from config import CHANNEL_BACKUP, CHANNEL_TEST
from data import get_source, get_sources_by_api_id
from model import SourceDisplay
from translation import translate


async def backup_single(client: Client, message: Message) -> str:
    msg_backup = await client.forward_messages(CHANNEL_BACKUP, message.chat.id, message.id)
    print("Backup single", msg_backup.link)
    return msg_backup.link


async def backup_multiple(client: Client, messages: [Message]) -> str:
    msg_ids = [message.id for message in messages]
    msg_backup = (await client.forward_messages(CHANNEL_BACKUP, messages[0].chat.id, msg_ids))[0]
    print("Backup multiple", msg_backup.link)
    return msg_backup.link


def format_text(text: str, message: Message, source: SourceDisplay, backup_link: str) -> str:
    name = source.display_name
    if source.bias is not None:
        name += f" {source.bias}"

    formatted = f"{text}\n\nQuelle: <a href='{message.link}'>{name}</a> |<a href='{backup_link}'> 💾 </a>"
    if source.detail_id is not None:
        formatted += f"|<a href='https://t.me/nn_sources/{source.detail_id}'> ℹ️ </a>"
    formatted += "\n\n👉 Folge @NYX_News für mehr!"

    return formatted


async def handle_text(client: Client, message: Message):
    print(message.chat.id, message.text)

    source = get_source(message.chat.id)

    text = format_text(translate(message.text), message, source, await backup_single(client, message))

    await client.send_message(703453307, text)


async def handle_single(client: Client, message: Message):
    print(message.chat.id, message.text)

    source = get_source(message.chat.id)

    text = format_text(translate(message.caption), message, source, await backup_single(client, message))

    await message.copy(703453307, caption=text)


async def handle_multiple(client: Client, message: Message):
    print(message.chat.id, message.text)

    source = get_source(message.chat.id)

    mg = await client.get_media_group(message.chat.id, message.id)

    text = format_text(
        translate(message.caption),
        message,
        source,
        await backup_multiple(client, mg))

    await client.copy_media_group(703453307, from_chat_id=message.chat.id, message_id=message.id, captions=text)


def start():
    apps = list()

    for a in account.accounts:
        print(f"Account {a.name} >>>>>")
        app = Client(
            name=a.name,
            api_id=a.api_id,
            api_hash=a.api_hash,
            phone_number=a.phone_number,
            #   phone_code=input(f"phone code {a.name}:"),
            password="area",
            parse_mode=ParseMode.HTML
        )
        sources = get_sources_by_api_id(a.api_id) + [CHANNEL_TEST]

        bf = filters.channel & filters.chat(sources) & filters.incoming
        mf = (filters.photo | filters.video | filters.animation)

        app.add_handler(MessageHandler(handle_multiple, filters=filters.media_group & filters.caption & mf & bf))
        app.add_handler(MessageHandler(handle_single, filters=filters.caption & mf & bf))
        app.add_handler(MessageHandler(handle_text, filters=filters.text & bf))

        apps.append(app)

    for app in apps:
        app.start()
    idle()


# for app in apps:
#    app.stop()


if __name__ == "__main__":
    start()
