import logging

import deepl
import regex as re
from deep_translator import GoogleTranslator, single_detection
from deepl import QuotaExceededException, SplitSentences
from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from config import DEEPL, GROUP_PATTERN
from constant import (PLACEHOLDER, PATTERN_REPLACEMENT, PATTERN_HTMLTAG, PATTERN_HASHTAG, emoji_space_pattern,
                      emoji_pattern, PATTERN_FITZPATRICK, REPLACEMENTS, PATTERN_PARAGRAPH)
from data import get_patterns, get_footer
from model import SourceDisplay

translator = deepl.Translator(DEEPL)

_bl_entries = [
    "Нічний чат, правила стандартні:",
    "paypal",
    "patreon"
]

BLACKLIST = re.compile(f"({')|('.join(_bl_entries)})", re.IGNORECASE)


def escape(string: str) -> str:
    return re.escape(string)  # .replace(' ',r'\s+')


# might also be able to handle too long posts for caption.
# just input a threshold parameter here, then send the rest in a separate message
def chunk_paragraphs(text: str) -> str:
    if len(text) <= 1200 and len(re.findall(f'\n\n', text)) < 5:
        return text

    res = []
    threshold = 440
    for chunk in re.split(PATTERN_PARAGRAPH, text):
        if res and len(chunk) + len(res[-1]) < threshold:
            res[-1] += f' {chunk}'
        else:
            res.append(f'{chunk}')
    return "\n\n".join(res)  # fixme: cuts random letters at the end of sentences that are within a paragraph


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

    translated_text = chunk_paragraphs(translated_text)

    logging.info(f"paragraphed ::::::: {translated_text}")

    return translated_text


def format_text(text: str, message: Message, source: SourceDisplay, backup_id: int) -> str:
    formatted = f"{text}\n\nQuelle: <a href='{message.link}'>{source.display_name}"
    if source.bias is not None:
        formatted += f" {source.bias}"
    formatted += f"</a> |<a href='https://t.me/nn_backup/{backup_id}'> 💾 </a>"

    if source.username is None and source.invite is not None:
        # todo: remove if detail added
        formatted += f"|<a href='https://t.me/+{source.invite}'> 🔗️ </a>"

    if source.detail_id is not None:
        formatted += f"|<a href='https://t.me/nn_sources/{source.detail_id}'> ℹ️ </a>"

    footer = get_footer(source.destination)
    if footer is not None:
        formatted += footer

    #   logging.info(f"-------------------------\n>>>>>>>> formatted:\n", formatted)
    return formatted


async def debloat_message(message: Message, client: Client) -> bool | str:
    if message.caption is not None:
        limit = 20
        text = message.caption.html
    else:
        text = message.text.html
        limit = 30

    if len(re.findall(BLACKLIST, text)) != 0:
        return False

    patterns = get_patterns(message.chat.id)

    text = PATTERN_HTMLTAG.sub("", text).rstrip()

    if patterns is not None and len(patterns) != 0:
        pat = [escape(re.sub(PATTERN_HTMLTAG, '', p)) for p in patterns]  # .replace(" ", r'\s*')
        pattern = fr"({')|('.join(pat)})"

        result = re.findall(pattern, text, flags=re.IGNORECASE)
        logging.info(f"Text ::: {text}")
        logging.info(f"clean_pattern__result ::: {result}")
        logging.info(pattern)

        if len(result) == 0:
            await message.forward(GROUP_PATTERN)
            await client.send_message(GROUP_PATTERN, text, parse_mode=ParseMode.DISABLED)

            logging.info(f"-- doesnt match --\n\n{text}\n\n---")
            return False  # comment out, if you want to send it despite not matching pattern, might bring in ads

        text = re.sub(pattern, "", text)

    text = re.sub(f"@{message.chat.username}$", "", text, flags=re.IGNORECASE).rstrip()
    # logging.info(f"<<<<< subbed  {text}")
    text = PATTERN_HASHTAG.sub("", text, ).rstrip()
    logging.info(f"<<<<< hashtag :  {text}")

    if len(re.findall(r"t\.me/\+", text)) != 0:
        logging.info(f">>>>>>>>> likely contains ad, please check! -- {message.link}")
        await client.send_message(GROUP_PATTERN, f">>>>>>>>> likely contains ad, please check! -- {message.link}",
                                  parse_mode=ParseMode.DISABLED)
        return False

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

    text = PATTERN_REPLACEMENT.sub(lambda m: REPLACEMENTS[re.escape(m.group(0))], text)

    logging.info(f"<<<<< spaced_BEFORE::: {text}", )

    text = translate(text)

    logging.info(f"--------------------------------------------------------\n\n------ TRANS -single {text, emojis}", )

    for emoji in emojis:
        text = re.sub(PLACEHOLDER, emoji, text, 1)

    logging.info(f"-------------------------\n>>>>>>>> translated_text:\n {text}")

    text = re.sub(PATTERN_FITZPATRICK, "", text, ).rstrip()

    return text
