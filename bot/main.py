import asyncio
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Final

from pyrogram import Client, filters, compose
from pyrogram.enums import ParseMode
from pyrogram.errors import MessageNotModified
from pyrogram.types import Message, InputMediaVideo, InputMediaPhoto, LinkPreviewOptions

from config import CHANNEL_BACKUP, CHANNEL_TEST, CHANNEL_UA, TESTING, PASSWORD, GROUP_LOG, CONTAINER
from db import get_source, get_source_ids_by_api_id, get_post, set_post, get_accounts
from militarnyi import get_militarnyi
from model import Post
from postillon import get_postillon
from translation import translate, debloat_text, format_text


def add_logging():
    if CONTAINER:
        # log_filename: Final[str] = rf"../logs/{datetime.now().strftime('%Y-%m-%d/%H-%M-%S')}.log"
        #   os.makedirs(os.path.dirname(log_filename), exist_ok=True)
        logging.basicConfig(
            format="%(asctime)s %(levelname)-5s %(funcName)-20s [%(filename)s:%(lineno)d]: %(message)s",
            encoding="utf-8",

            level=logging.INFO,
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.StreamHandler(),
                #   logging.FileHandler(log_filename)
            ],
            force=True,
        )

    else:
        log_filename: Final[str] = rf"../logs/{datetime.now().strftime('%Y-%m-%d/%H-%M-%S')}.log"
        os.makedirs(os.path.dirname(log_filename), exist_ok=True)
        logging.basicConfig(
            format="%(asctime)s %(levelname)-5s %(funcName)-20s [%(filename)s:%(lineno)d]: %(message)s",
            encoding="utf-8",
            filename=log_filename,
            level=logging.INFO,
            datefmt='%Y-%m-%d %H:%M:%S',
            force=True,
        )

    logging.getLogger("httpx").setLevel(logging.WARNING)


async def backup_single(client: Client, message: Message) -> int:
    msg_backup = await client.forward_messages(CHANNEL_BACKUP, message.chat.id, message.id)
    logging.debug(f"Backup singl: {msg_backup.link}", )
    return msg_backup.id


async def backup_multiple(client: Client, messages: List[Message]) -> int:
    msg_ids = [message.id for message in messages]
    msg_backup = (await client.forward_messages(CHANNEL_BACKUP, messages[0].chat.id, msg_ids))[0]
    logging.debug(f"Backup multiple: {msg_backup.link}", )
    return msg_backup.id


def list_dir_tree(start_path):
    for root, dirs, files in os.walk(start_path):
        # Determine indentation level
        level = root.replace(start_path, '').count(os.sep)
        indent = ' ' * 4 * level
        # Print folder name
        print(f'{indent}{os.path.basename(root)}/')
        sub_indent = ' ' * 4 * (level + 1)
        # Print files in the folder
        for f in files:
            print(f'{sub_indent}{f}')


async def main():
    add_logging()

    print(f"Running PRINT ...")
    logging.info(f"Running LOGGING ...")

    apps = list()
    accounts = await get_accounts()
    logging.info(f"Accounts: {accounts}")

    for a in accounts:
        print(f"Account {a.name} >>>>>")
        logging.info(f"Account {a.name} >>>>>")

        app = Client(
            name=a.name,
            api_id=a.api_id,
            api_hash=a.api_hash,
            phone_number=a.phone_number,
            password=PASSWORD,
            lang_code="de",
            parse_mode=ParseMode.HTML,
            #     workdir="/sessions"
        )

        sources = await get_source_ids_by_api_id(a.api_id)

        if not TESTING:
            remove_sources = [CHANNEL_TEST, -1001011817559, -1001123527809]

            for channel_id in remove_sources:
                while channel_id in sources:
                    sources.remove(channel_id)

        if TESTING and a.name == "Michael":
            @app.on_message(filters.caption & filters.chat([CHANNEL_TEST, -1001011817559]) & filters.photo)
            async def test_video(client: Client, message: Message):
                backup_id = await backup_single(client, message)
                # await client.send_message(CHANNEL_TEST, "Artikel lädt [der Download von Videos/Bildern dauert etwas]")

                cp = await get_militarnyi(message)

                source = await get_source(message.chat.id)

                medias = list()
                for v in cp.video_urls:
                    medias.append(InputMediaVideo(v))
                for v in cp.image_urls:
                    medias.append(InputMediaPhoto(v))
                medias[0].caption = await format_text(translate(cp.caption), message, source, backup_id)

                msg = (await client.send_media_group(CHANNEL_UA, medias))[0]

                for text in cp.texts:
                    text = await  format_text(translate(text), message, source, backup_id)
                    msg = await client.send_message(CHANNEL_UA, text, reply_to_message_id=msg.id,
                                                    disable_web_page_preview=True)

                for f in cp.image_urls + cp.image_urls:
                    Path(f).unlink(missing_ok=True)

        if TESTING and a.name == "Martin":
            @app.on_message(filters.chat([CHANNEL_TEST]) & filters.inline_keyboard)  # , -1001123527809
            async def handle_postillion(client: Client, message: Message):
                print("postillon", message)

                backup_id = await backup_single(client, message)
                #  await client.send_message(CHANNEL_TEST, "Artikel lädt [der Download von Videos/Bildern dauert etwas]")

                cp = await get_postillon(message)

                print("postillon")

                source = await get_source(message.chat.id)

                msg = await client.send_photo(source.destination,
                                              cp.image_urls[0],
                                              await     format_text(cp.caption, message, source, backup_id)
                                              )

        bf = filters.channel & filters.chat(sources) & ~filters.forwarded & filters.incoming
        mf = bf & (filters.photo | filters.video | filters.animation)

        @app.on_message(filters.text & bf)
        async def new_text(client: Client, message: Message):
            logging.info(f">>>>>> {client.name}: handle_text {message.chat.id, message.text.html}", )

            source = await get_source(message.chat.id)

            text = await debloat_text(message, client)
            if not text:
                return

            logging.info(f"T X -single {text}", )

            backup_id = await backup_single(client, message)
            text = await format_text(text, message, source, backup_id)

            if message.reply_to_message_id is not None:
                reply_post = await get_post(message.chat.id, message.reply_to_message_id)
                if reply_post is None:
                    reply_id = None
                else:
                    reply_id = reply_post.message_id
            else:
                reply_id = None

            logging.info(f"send New Text {client.name}")
            msg = await client.send_message(source.destination, text,
                                            link_preview_options=LinkPreviewOptions(is_disabled=True))

            await set_post(Post(
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
            logging.info(f">>>>>> {client.name}: edit_text {message.chat.id, message.text.html}", )

            if message.date < (datetime.now() - timedelta(weeks=1)):
                return

            await asyncio.sleep(60)
            post = await get_post(message.chat.id, message.id)

            if post is None:
                await new_text(client, message)
                return

            source = await get_source(message.chat.id)

            text = await debloat_text(message, client)
            if not text:
                return

            logging.info(f"edit text::: {post}", )

            text = await format_text(text, message, source, post.backup_id)
            try:
                await client.edit_message_text(post.destination, post.message_id, text, disable_web_page_preview=True)
            except MessageNotModified:
                pass

        @app.on_message(filters.media_group & filters.caption & mf)
        async def new_multiple(client: Client, message: Message):
            logging.info(f">>>>>> {client.name}: handle_multiple {message.chat.id, message.caption.html}", )

            source = await get_source(message.chat.id)

            text = await debloat_text(message, client)
            if not text:
                return

            mg = await client.get_media_group(message.chat.id, message.id)
            backup_id = await backup_multiple(client, mg)
            if not source.is_spread:
                return

            text = await format_text(text, message, source, backup_id)

            if message.reply_to_message_id is not None:
                reply_post = await get_post(message.chat.id, message.reply_to_message_id)
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

            await set_post(Post(
                msgs[0].chat.id,
                msgs[0].id,
                message.chat.id,
                message.id,
                backup_id,
                reply_id,
                text
            ))

        @app.on_message(filters.caption & mf)
        async def new_single(client: Client, message: Message):
            logging.info(f">>>>>> {client.name}: handle_single {message.chat.id}")

            source = await get_source(message.chat.id)

            text = await debloat_text(message, client)
            if not text:
                return

            backup_id = await backup_single(client, message)
            if not source.is_spread:
                return

            logging.info(f">>>>>> {client.name}: handle_single {source, message.chat.id, backup_id}")
            text = await format_text(text, message, source, backup_id)

            if message.reply_to_message_id is not None:
                reply_post = await  get_post(message.chat.id, message.reply_to_message_id)
                if reply_post is None:
                    reply_id = None

                else:
                    reply_id = reply_post.message_id
            else:
                reply_id = None

            logging.info(f"---- new single {client.name}----- {source}")
            msg = await message.copy(source.destination, caption=text)  # media caption too long

            await set_post(Post(
                msg.chat.id,
                msg.id,
                message.chat.id,
                message.id,
                backup_id,
                reply_id,
                text
            ))

            logging.info(f"----------------------------------------------------")

        @app.on_edited_message(filters.caption & mf)
        async def edit_caption(client: Client, message: Message):
            logging.info(f">>>>>> {client.name}: edit_caption {message.chat.id, message.caption.html}", )

            if message.date < (datetime.now() - timedelta(weeks=1)):
                return

            await asyncio.sleep(60)
            post = await get_post(message.chat.id, message.id)

            if post is None:
                if message.media_group_id is None:
                    await new_single(client, message)
                else:
                    await new_multiple(client, message)
                return

            source = await get_source(message.chat.id)

            text = await debloat_text(message, client)
            if not text:
                return

            text = await format_text(text, message, source, post.backup_id)

            try:
                logging.info(f"edit_caption ::::::::::::::::::::: {post}", )
                await client.edit_message_caption(post.destination, post.message_id, text)
            except MessageNotModified:
                pass

        @app.on_message(filters.command("join"))
        async def handle_join(client: Client, message: Message):

            args = message.text.split(" ")[1:]
            joined_chat = args[0]
            joined_by = args[1]
            logging.info(f"join to {joined_chat} by user {joined_by} via {message.from_user.id}")

            if len(args) < 2:
                await message.reply_text(f"/join {joined_chat} {joined_by} ARGS_DONT_MATCH")
                await client.send_message(GROUP_LOG, message_thread_id=489,
                                          text=f"ARGS_DONT_MATCH {joined_chat} {joined_by}\n\n{message.text}")

            try:
                chat = await client.join_chat(joined_chat)

                await message.reply_text(f"/join {joined_chat} {joined_by} JOIN_SUCCESS")
                await client.send_message(GROUP_LOG, message_thread_id=489,
                                          text=f"Joined {joined_chat} {joined_by}\n\n{chat}")
            except Exception as e:
                await message.reply_text(f"/join {joined_chat} {joined_by} JOIN_FAILED")
                await client.send_message(GROUP_LOG, message_thread_id=489,
                                          text=f"ERROR Joining {joined_chat} {joined_by}\n\n{e}")

        @app.on_message(filters.command("leave"))
        async def handle_leave(client: Client, message: Message):
            logging.info(f"leave by user {message.from_user.id}")

            chat = await client.leave_chat(message.text.split(" ")[1])
            await message.reply_text(f"Tried to leave. Result:\n\n{chat}")

        apps.append(app)

    try:
        await compose(apps)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    asyncio.run(main())
