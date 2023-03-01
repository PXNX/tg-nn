import asyncio
import os
import re
from datetime import datetime
from pathlib import Path

from pyrogram import Client, filters, compose
from pyrogram.enums import ParseMode
from pyrogram.errors import MessageNotModified
from pyrogram.types import Message, InputMediaVideo, InputMediaPhoto

import account
from config import CHANNEL_BACKUP, CHANNEL_TEST, GROUP_PATTERN, CHANNEL_UA
from constant import HASHTAG, FLAG_EMOJI, PLACEHOLDER, REPLACEMENTS
from crawl_iiss import try_url
from data import get_source, get_source_ids_by_api_id, get_patterns, get_post, set_post
from model import SourceDisplay, Post
from translation import translate

LOG_FILENAME = rf"C:\Users\Pentex\PycharmProjects\tg-nn\logs\{datetime.now().strftime('%Y-%m-%d')}\{datetime.now().strftime('%H-%M-%S')}.out"
os.makedirs(os.path.dirname(LOG_FILENAME), exist_ok=True)

# logging.basicConfig(
#   format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)s - %(funcName)20s()]: %(message)s ",
#  level=logging.INFO, filename=LOG_FILENAME
# )

BLACKLIST = [
    "Нічний чат, правила стандартні:"
]


async def backup_single(client: Client, message: Message) -> int:
    msg_backup = await client.forward_messages(CHANNEL_BACKUP, message.chat.id, message.id)
    #   print("Backup single", msg_backup.link)
    return msg_backup.id


async def backup_multiple(client: Client, messages: [Message]) -> int:
    msg_ids = [message.id for message in messages]
    msg_backup = (await client.forward_messages(CHANNEL_BACKUP, messages[0].chat.id, msg_ids))[0]
    #  print("Backup multiple", msg_backup.link)
    return msg_backup.id


def format_text(text: str, message: Message, source: SourceDisplay, backup_id: int) -> str:
    name = source.display_name
    if source.bias is not None:
        name += f" {source.bias}"

    formatted = f"{text}\n\nQuelle: <a href='{message.link}'>{name}</a> |<a href='https://t.me/nn_backup/{backup_id}'> 💾 </a>"
    if source.username is None and source.invite is not None:
        # remove if detail added
        formatted += f"|<a href='https://t.me/+{source.invite}'> 🔗️ </a>"
    if source.detail_id is not None:
        formatted += f"|<a href='https://t.me/nn_sources/{source.detail_id}'> ℹ️ </a>"
    formatted += "\n\n👉 Folge @NYX_News für mehr!"

    #   print("-------------------------\n>>>>>>>> formatted:\n", formatted)
    return formatted


async def debloat_text(message: Message, client: Client) -> bool | str:
    patterns = get_patterns(message.chat.id)

    if message.caption is not None:
        limit = 60
        text = message.caption.html
    else:
        text = message.text.html
        limit = 150

    if text in BLACKLIST:
        return False

    if patterns is not None and len(patterns) != 0:
        pattern = f"({')|('.join([re.escape(p) for p in patterns])})"

        result = re.findall(pattern, text)

        if len(result) == 0:
            await message.forward(GROUP_PATTERN)
            await client.send_message(GROUP_PATTERN, text, parse_mode=ParseMode.DISABLED)

            print("doesnt match\n\n--")
            return False

        text = re.sub(pattern, text, "")

    text = re.sub(r"<(?!\/?a(?=>|\s.*>))\/?.*?>", "", text)
    text = re.sub(f"@{message.chat.username}$", "", text.rstrip())
    emojis = re.findall(FLAG_EMOJI, text)
    text = re.sub(FLAG_EMOJI, PLACEHOLDER, re.sub(HASHTAG, "", text)).rstrip()
    print("-------------------------\n>>>>>>>> sub_text:\n", text)

    rep = dict((re.escape(k), v) for k, v in REPLACEMENTS.items())
    pattern = re.compile("|".join(rep.keys()))
    text = pattern.sub(lambda m: rep[re.escape(m.group(0))], text)

    if len(text) < limit:
        return False

    translated_text = translate(text)

    for emoji in emojis:
        translated_text = re.sub(PLACEHOLDER, emoji, translated_text, 1)
    #  print("translated_text", text)

    print("-------------------------\n>>>>>>>> translated_text:\n", translated_text)
    return translated_text


async def main():
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

        sources = get_source_ids_by_api_id(a.api_id) + [CHANNEL_TEST]
        if -1001011817559 in sources:
            sources.remove(-1001011817559)  # because Militarnij has its own function

        bf = filters.channel & filters.chat(sources) & filters.incoming & ~filters.forwarded
        mf = bf & (filters.photo | filters.video | filters.animation)

        @app.on_message(filters.text & bf)
        async def new_text(client: Client, message: Message):
            print(">>>>>> handle_text", message.chat.id, message.text.html)

            source = get_source(message.chat.id)

            text = await debloat_text(message, client)
            if not text:
                return

            backup_id = await backup_single(client, message)
            text = format_text(text, message, source, backup_id)

            if message.reply_to_message_id is not None:
                reply_post = get_post(message.chat.id, message.reply_to_message_id)
                if reply_post is None:
                    reply_id = None
                else:
                    reply_id = reply_post.message_id
            else:
                reply_id = None

            print("send New Text", client.name)
            msg = await client.send_message(source.destination, text, disable_web_page_preview=True)

            set_post(Post(
                msg.chat.id,
                msg.id,
                message.chat.id,
                message.id,
                backup_id,
                reply_id,
                text
            ))

        @app.on_edited_message(filters.text & bf)
        async def edit_text(client: Client, message: Message):
            print(">>>>>> edit_text", message.chat.id, message.text.html)

            post = get_post(message.chat.id, message.id)

            if post is None:
                #  await asyncio.sleep(5)
                #   await new_text(client, message)
                return

            source = get_source(message.chat.id)

            text = await debloat_text(message, client)
            if not text:
                return

            print("edit text:::", post)

            text = format_text(text, message, source, post.backup_id)
            try:
                await client.edit_message_text(post.destination, post.message_id, text, disable_web_page_preview=True)
            except MessageNotModified:
                pass

        @app.on_message(filters.caption & mf)
        async def new_single(client: Client, message: Message):
            print(">>>>>> handle_single", message.chat.id, message.caption.html)

            source = get_source(message.chat.id)

            text = await debloat_text(message, client)
            if not text:
                return

            backup_id = await backup_single(client, message)
            text = format_text(text, message, source, backup_id)

            if message.reply_to_message_id is not None:
                reply_post = get_post(message.chat.id, message.reply_to_message_id)
                if reply_post is None:
                    reply_id = None
                else:
                    reply_id = reply_post.message_id
            else:
                reply_id = None

            print("---- new single", client.name, "-----", source)
            msg = await message.copy(source.destination, caption=text)  # media caption too long

            set_post(Post(
                msg.chat.id,
                msg.id,
                message.chat.id,
                message.id,
                backup_id,
                reply_id,
                text
            ))

            print("----------------------------------------------------")

        #   print(">>>>>>>>>>>>>>>>>>>>> file_id ::::::::::::", message.photo.file_id)
        #  print(">>>>>>>>>>>>>>>>>>>>> file_unique_id ::::::::::::", message.photo.file_unique_id)

        @app.on_message(filters.media_group & filters.caption & mf)
        async def new_multiple(client: Client, message: Message):
            print(">>>>>> handle_multiple", message.chat.id, message.caption.html)

            source = get_source(message.chat.id)

            text = await debloat_text(message, client)
            if not text:
                return

            mg = await client.get_media_group(message.chat.id, message.id)

            backup_id = await backup_multiple(client, mg)
            text = format_text(text, message, source, backup_id)

            if message.reply_to_message_id is not None:
                reply_post = get_post(message.chat.id, message.reply_to_message_id)
                if reply_post is None:
                    reply_id = None
                else:
                    reply_id = reply_post.message_id
            else:
                reply_id = None

            msgs = await client.copy_media_group(source.destination,
                                                 from_chat_id=message.chat.id,
                                                 message_id=message.id,
                                                 captions=text)

            set_post(Post(
                msgs[0].chat.id,
                msgs[0].id,
                message.chat.id,
                message.id,
                backup_id,
                reply_id,
                text
            ))

        @app.on_edited_message(filters.caption & mf)
        async def edit_caption(client: Client, message: Message):
            print(">>>>>> edit_caption", message.chat.id, message.caption.html)

            post = get_post(message.chat.id, message.id)

            if post is None:
                #   await asyncio.sleep(5)
                #    if message.media_group_id is None:
                #       await new_single(client, message)
                #   else:
                #       await new_multiple(client, message)
                return

            source = get_source(message.chat.id)

            text = await debloat_text(message, client)
            if not text:
                return

            text = format_text(text, message, source, post.backup_id)

            try:
                print("edit_caption :::::::::::::::::::::", post)
                await client.edit_message_caption(post.destination, post.message_id, text)
            except MessageNotModified:
                pass

        if app.name == "Michael":
            @app.on_message(filters.caption & filters.chat([CHANNEL_TEST, -1001011817559]) & filters.photo)
            async def test_video(client: Client, message: Message):
                backup_id = await backup_single(client, message)
                #  await client.send_message(CHANNEL_TEST, "Artikel lädt [der Download von Videos/Bildern dauert etwas]")

                CHANNEL = CHANNEL_UA

                cp = await try_url(message)

                source = get_source(message.chat.id)

                medias = list()
                for v in cp.video_urls:
                    medias.append(InputMediaVideo(v))
                for v in cp.image_urls:
                    medias.append(InputMediaPhoto(v))
                medias[0].caption = format_text(translate(cp.caption), message, source, backup_id)

                msg = (await client.send_media_group(CHANNEL, medias))[0]

                for text in cp.texts:
                    text = format_text(translate(text), message, source, backup_id)
                    msg = await client.send_message(CHANNEL, text, reply_to_message_id=msg.id,
                                                    disable_web_page_preview=True)

                for f in cp.image_urls + cp.image_urls:
                    Path(f).unlink(missing_ok=True)

        apps.append(app)

    await compose(apps)


if __name__ == "__main__":
    asyncio.run(main())
