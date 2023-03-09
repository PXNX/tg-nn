import regex as re

PATTERN_HASHTAG = re.compile(r"(\s*#\S*)*$")
PATTERN_HTMLTAG = re.compile(r"<[^a>]+>")
# FLAG_EMOJI = re.compile(u"🏴|🏳️|[\U0001F1E6-\U0001F1FF]{2}|<\/?a[^>]*>", re.UNICODE)  # 🏴|🏳️|([🇦-🇿]{2})|( ##|\n{2,}
emoji_space_pattern = re.compile(r"([‼\p{So}])([^\s‼\p{So}]+)", flags=re.UNICODE)
emoji_pattern = re.compile(r"[‼\p{So}]|(?:<\/?a[^>]*>)", flags=re.UNICODE)

PLACEHOLDER = '<body>'  # ║ #▓

REPLACEMENTS = {
    "ЗСУ": "Збро́йні си́ли Украї́ни",
}
REPLACEMENTS = {re.escape(k): v for k, v in REPLACEMENTS.items()}
PATTERN_REPLACEMENT = re.compile("|".join(REPLACEMENTS.keys()), flags=re.IGNORECASE)
REPLACEMENT = lambda m: REPLACEMENTS[re.escape(m.group(0))]
