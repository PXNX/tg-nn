import re

HASHTAG = re.compile(r"(\s*#\w+)*$")
FLAG_EMOJI = re.compile(u"🏴|🏳️|[\U0001F1E6-\U0001F1FF]{2}|<\/?a[^>]*>", re.UNICODE)  # 🏴|🏳️|([🇦-🇿]{2})|( ##|\n{2,}
PLACEHOLDER = '▓'  # ║

REPLACEMENTS = {
    "ЗСУ": "Збро́йні си́ли Украї́ни",

}
