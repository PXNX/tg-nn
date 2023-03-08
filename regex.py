import re

ESCAPES = {
    r"|": r"\|",
    r".": r"\.",
    r"+": ""
}

pat = fr"""<a\ href="https://t\.me/\+N7Vldq9puSkxOWEy">Підписатись\ на\ 24\ канал</a>"""
print(pat)
#pat= re.escape(r"""<a href="https://t.me/+N7Vldq9puSkxOWEy">Підписатись на 24 Канал</a>""")

print(pat)

txt = fr"""⚡️<b>Поліція розганяє мітингувальників біля будівлі парламенту в Грузії

</b><i>Фото: Mzia Saganelidze RFE/RL

</i><a href="https://t.me/+N7Vldq9puSkxOWEy">Підписатись на 24 Канал</a>"""

res = re.sub(pat, "", txt,flags=re.IGNORECASE)

print(res)

HTML_TAG = re.compile(r'<[^a>]+>')