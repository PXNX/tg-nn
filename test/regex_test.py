import regex as re

ESCAPES = {
    r"|": r"\|",
    r".": r"\.",
    r"+": ""
}

pat = re.compile(r"([‼|\p{So}])", re.IGNORECASE)
print(pat)
# pat= re.escape(r"""<a href="https://t.me/+N7Vldq9puSkxOWEy">Підписатись на 24 Канал</a>""")

print(pat)

txt = fr""" 🇪🇸Евросоюз в лице Жозепа Борреля вмешался во внутренние дела Грузии:

«Во вторник парламент Грузии принял в первом чтении новый закон о прозрачности иностранного влияния. Это очень плохое развитие событий для Грузии🏴 и ее народа. Закон несовместим с ценностями и стандартами ЕС. ‼️Это противоречит заявленной цели Грузии по вступлению в Европейский союз»

anschließen sollte ". ;.

Dmytro Bastrakov teilte seine Eindrücke von der Reise, <a href="https://censor.net/ua/n3404131">bei der er die Leiche seines Handlangers mitnahm, der von den Verteidigern der Ukraine eliminiert wurde</a>.

„🐟Von Donezk bis Rostow, von Leich

Russia

<a href="http://google.com/">Dmytro Bastrakov teilte seine Eindrücke von der Reise, </a><a href="https://censor.net/ua/n3404131">bei der er die Leiche seines Handlangers mitnahm, der von den Verteidigern der Ukraine eliminiert wurde</a>.

„Von Donezk bis Rostow, von Leich"""

res = re.sub(pat, "", txt)

print(res)
