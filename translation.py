import deepl
from deep_translator import GoogleTranslator
from deepl import QuotaExceededException

from config import DEEPL

translator = deepl.Translator(DEEPL)


def translate(text: str) -> str:
    try:
        translated_text = translator.translate_text(text, target_lang="de", tag_handling="html",
                                                    preserve_formatting=True).text
    except QuotaExceededException:
        print("--- Quota exceeded ---")
        translated_text = GoogleTranslator(source='auto', target="de").translate(text=text)
        pass
    except Exception as e:
        print("--- other error translating --- ", e)
        translated_text = GoogleTranslator(source='auto', target="de").translate(text=text)
        pass

    return translated_text
