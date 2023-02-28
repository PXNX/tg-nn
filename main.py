import asyncio
import os
import re
from pathlib import Path

from pyrogram import Client, filters, compose
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InputMediaVideo, InputMediaPhoto

import account
from config import CHANNEL_BACKUP, CHANNEL_TEST, GROUP_PATTERN, CHANNEL_UA
from constant import HASHTAG, FLAG_EMOJI, PLACEHOLDER, REPLACEMENTS
from crawl_iiss import try_url
from data import get_source, get_source_ids_by_api_id, get_patterns, get_post, set_post
from model import SourceDisplay, Post
from translation import translate


async def backup_single(client: Client, message: Message) -> int:
    msg_backup = await client.forward_messages(CHANNEL_BACKUP, message.chat.id, message.id)
    print("Backup single", msg_backup.link)
    return msg_backup.id


async def backup_multiple(client: Client, messages: [Message]) -> int:
    msg_ids = [message.id for message in messages]
    msg_backup = (await client.forward_messages(CHANNEL_BACKUP, messages[0].chat.id, msg_ids))[0]
    print("Backup multiple", msg_backup.link)
    return msg_backup.id


def format_text(text: str, message: Message, source: SourceDisplay, backup_id: int) -> str:
    name = source.display_name
    if source.bias is not None:
        name += f" {source.bias}"

    formatted = f"{text}\n\nQuelle: <a href='{message.link}'>{name}</a> |<a href='https://t.me/nn_backup/{backup_id}'> 💾 </a>"
    if source.detail_id is not None:
        formatted += f"|<a href='https://t.me/nn_sources/{source.detail_id}'> ℹ️ </a>"
    formatted += "\n\n👉 Folge @NYX_News für mehr!"

    print("-------------------------\n>>>>>>>> formatted:\n", formatted)
    return formatted


async def debloat_text(message: Message, client: Client) -> bool | str:
    patterns = get_patterns(message.chat.id)

    if message.caption is not None:
        text = message.caption.html
    else:
        text = message.text.html

    if patterns is not None and not any(p in text for p in patterns):
        await message.forward(GROUP_PATTERN)
        await client.send_message(GROUP_PATTERN, text, parse_mode=ParseMode.DISABLED)
        return False

    for p in patterns:
        text = re.sub(p, "", text)
    text = re.sub(r"<(?!\/?a(?=>|\s.*>))\/?.*?>", "", text)
    text = re.sub(f"@{message.chat.username}$", "", text)
    emojis = re.findall(FLAG_EMOJI, text)
    text = re.sub(FLAG_EMOJI, PLACEHOLDER, re.sub(HASHTAG, "", text)).rstrip()
    print("-------------------------\n>>>>>>>> sub_text:\n", text)

    rep = dict((re.escape(k), v) for k, v in REPLACEMENTS.items())
    pattern = re.compile("|".join(rep.keys()))
    text = pattern.sub(lambda m: rep[re.escape(m.group(0))], text)

    translated_text = translate(text)

    for emoji in emojis:
        translated_text = re.sub(PLACEHOLDER, emoji, translated_text, 1)
    print("translated_text", text)

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
        bf = filters.channel & filters.chat(sources) & filters.incoming
        mf = (filters.photo | filters.video | filters.animation) & ~filters.forwarded

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
                reply_id = get_post(message.chat.id, message.reply_to_message_id).message_id
            else:
                reply_id = None

            msg = await client.send_message(703453307, text, disable_web_page_preview=True)

            set_post(Post(
                703453307,
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
            source = get_source(message.chat.id)

            text = await debloat_text(message, client)
            if not text:
                return

            text = format_text(text, message, source, post.backup_id)

            await client.edit_message_text(703453307, post.message_id, text)

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

            msg = (await client.send_media_group( CHANNEL, medias))[0]

            for text in cp.texts:
                text = format_text(translate(text), message, source, backup_id)
                msg = await client.send_message( CHANNEL, text, reply_to_message_id=msg.id,
                                                disable_web_page_preview=True)

            for f in cp.image_urls + cp.image_urls:
                Path(f).unlink(missing_ok=True)
        @app.on_message(filters.caption & mf & bf)
        async def new_single(client: Client, message: Message):
            print(">>>>>> handle_single", message.chat.id, message.caption.html)

            source = get_source(message.chat.id)

            text = await debloat_text(message, client)
            if not text:
                return

            backup_id = await backup_single(client, message)
            text = format_text(text, message, source, backup_id)

            if message.reply_to_message_id is not None:
                reply_id = get_post(message.chat.id, message.reply_to_message_id).message_id
            else:
                reply_id = None

            msg = await message.copy(703453307, caption=text)

            set_post(Post(
                703453307,
                msg.id,
                message.chat.id,
                message.id,
                backup_id,
                reply_id,
                text
            ))

            print("----------------------------------------------------")
            print(">>>>>>>>>>>>>>>>>>>>> file_id ::::::::::::", message.photo.file_id)
            print(">>>>>>>>>>>>>>>>>>>>> file_unique_id ::::::::::::", message.photo.file_unique_id)

        @app.on_message(filters.media_group & filters.caption & mf & bf)
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
                reply_id = get_post(message.chat.id, message.reply_to_message_id).message_id
            else:
                reply_id = None

            msgs = await client.copy_media_group(703453307, from_chat_id=message.chat.id, message_id=message.id,
                                                 captions=text)

            set_post(Post(
                703453307,
                msgs[0].id,
                message.chat.id,
                message.id,
                backup_id,
                reply_id,
                text
            ))

        @app.on_edited_message(filters.caption & mf & bf)
        async def edit_caption(client: Client, message: Message):
            print(">>>>>> edit_caption", message.chat.id, message.caption.html)

            post = get_post(message.chat.id, message.id)
            source = get_source(message.chat.id)

            text = await debloat_text(message, client)
            if not text:
                return

            text = format_text(text, message, source, post.backup_id)

            await client.edit_message_caption(703453307, post.message_id, text)



        apps.append(app)
    await compose(apps)


if __name__ == "__main__":
    asyncio.run(main())
