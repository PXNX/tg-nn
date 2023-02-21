import re

HASHTAG = re.compile(r"(\s*#\w+)*$")
FLAG_EMOJI = re.compile(r"🏴|🏳️|([🇦-🇿]{2})")  # 🏴|🏳️|([🇦-🇿]{2})|( ##|\n{2,}
PLACEHOLDER = '▓'  # ║

REPLACEMENTS = {
    "ЗСУ", "Збро́йні си́ли Украї́ни",

}


