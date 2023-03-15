import logging

import deepl
import regex as re
from deep_translator import GoogleTranslator
from deepl import QuotaExceededException, SplitSentences
from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from config import DEEPL, GROUP_PATTERN
from constant import PLACEHOLDER, REPLACEMENT, PATTERN_REPLACEMENT, PATTERN_HTMLTAG, \
    PATTERN_HASHTAG, emoji_space_pattern, emoji_pattern, PATTERN_FITZPATRICK
from data import get_patterns
from model import SourceDisplay

translator = deepl.Translator(DEEPL)

BLACKLIST = [
    "Нічний чат, правила стандартні:"
]


def escape(string: str) -> str:
    return re.escape(string)  # .replace(' ',r'\s+')


def translate(text: str) -> str:
    try:

        translated_text = translator.translate_text(text,
                                                    target_lang="de",
                                                    split_sentences=SplitSentences.ALL,
                                                    tag_handling="html",
                                                    #     preserve_formatting=True
                                                    ).text
    except QuotaExceededException:
        logging.info("--- Quota exceeded ---")
        translated_text = GoogleTranslator(source='auto', target="de").translate(text=text)
        pass
    except Exception as e:
        logging.error(f"--- other error translating --- {e}")
        translated_text = GoogleTranslator(source='auto', target="de").translate(text=text)
        pass

    return translated_text


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

    #   logging.info(f"-------------------------\n>>>>>>>> formatted:\n", formatted)
    return formatted


async def debloat_message(message: Message, client: Client) -> bool | str:
    if message.caption is not None:
        limit = 40
        text = message.caption.html
    else:
        text = message.text.html
        limit = 100

    if text in BLACKLIST:
        return False

    patterns = get_patterns(message.chat.id)

    if patterns is not None and len(patterns) != 0:
        pattern = fr"({')|('.join([escape(p) for p in patterns])})"

        result = re.findall(pattern, text, flags=re.IGNORECASE)
        logging.info(f"clean_pattern__result {text, result}")
        logging.info(pattern)

        if len(result) == 0:
            await message.forward(GROUP_PATTERN)
            await client.send_message(GROUP_PATTERN, text, parse_mode=ParseMode.DISABLED)

            logging.info(f"-- doesnt match\n\n--")
            return False  # comment out, if you want to send it despite not matching pattern, might bring in ads

        text = re.sub(pattern, "", text)

    text = PATTERN_HTMLTAG.sub("", text).rstrip()
    text = re.sub(f"@{message.chat.username}$", "", text, flags=re.IGNORECASE).rstrip()
    logging.info(f"<<<<< subbed  {text}")
    text = PATTERN_HASHTAG.sub("", text, ).rstrip()
    logging.info(f"<<<<< hashtag :  {text}")

    if len(text) < limit:
        logging.info(f"Text too short - limit: {limit}")
        return False

    return text


async def debloat_text(message: Message, client: Client) -> bool | str:
    text = await debloat_message(message, client)

    if not text:
        return False

    logging.info(f"clean_pattern  {text}")

    text = re.sub(emoji_space_pattern, r"\1 \2", text)
    logging.info(f"<<<<< spaced  {text}")

    #    emoji.get_emoji_list["en"]
    # emoji.replace_emoji('Python is 👍', replace='')

    emojis = emoji_pattern.findall(text)
    logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> emoijis: {emojis}")
    text = emoji_pattern.sub(PLACEHOLDER, text).rstrip()
    logging.info(f">>>>>>>>>> placeholder  {text}")

    text = PATTERN_REPLACEMENT.sub(REPLACEMENT, text)

    logging.info(f"<<<<< spaced_BEFORE::: {text}", )

    text = translate(text)

    logging.info(f"--------------------------------------------------------\n\n------ TRANS -single {text, emojis}", )

    for emoji in emojis:
        text = re.sub(PLACEHOLDER, emoji, text, 1)

    logging.info(f"-------------------------\n>>>>>>>> translated_text:\n {text}")

    text = re.sub(PATTERN_FITZPATRICK, "", text, ).rstrip()

    return text
