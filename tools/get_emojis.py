import httpx
from bs4 import BeautifulSoup


def extract_emojis(url: str) -> dict:
    output = {}
    response = httpx.get(url)
    #  response.raise_for_status()
    print("---")
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table')
    names = [n.text for n in table.find_all(attrs={"class": "name"})]
    codes = [c.text for c in table.find_all(attrs={"class": "code"})]
    for name, code in zip(names, codes):
        """
        replace semi-colons, commas, open smart quote, close smart quote,
        and asterisk (⊛) symbol used to denote newly added emojis,
        replace spaces after trimming for the asterisk case
        """
        name = name.removeprefix('flag: ') \
            .replace(':', '') \
            .replace(',', '') \
            .replace(u'\u201c', '') \
            .replace(u'\u201d', '') \
            .replace(u'\u229b', '') \
            .strip() \
            .replace(' ', '_')

        _code = []
        for c in code.split(' '):
            if len(c) == 6:
                _code.append(c.replace('U+', '\\U0000'))
            else:
                _code.append(c.replace('U+', '\\U000'))
            code = ''.join(_code)
        output[name] = code
    return output


emoji_url = 'https://www.unicode.org/emoji/charts/full-emoji-list.html'
emoji_modifiers_url = 'https://www.unicode.org/emoji/charts/full-emoji-modifiers.html'

print(".")
emojis = extract_emojis(emoji_url)
print(".")
emoji_modifiers = extract_emojis(emoji_modifiers_url)
total = emojis | emoji_modifiers

for emoji_name, emoji_code in sorted(total.items()):
    print(f"    u':{emoji_name}:': u'{emoji_code}'", end=',\n')
print('\nTotal count of emojis: ', len(total))
