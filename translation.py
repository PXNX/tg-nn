import deepl
from deep_translator import GoogleTranslator
from deepl import QuotaExceededException, SplitSentences

from config import DEEPL

translator = deepl.Translator(DEEPL)


def translate(text: str) -> str:
    translated_text = GoogleTranslator(source='auto', target="de").translate(text=text)
    print("TX:::::",translated_text)

    try:


      translated_text = translator.translate_text(text, target_lang="de",split_sentences=SplitSentences.ALL, tag_handling="html",
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
