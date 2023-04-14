import unittest

from translation import chunk_paragraphs

LOREM = """🇺🇸 Der frühere US-Präsident Clinton bedauert, dass er die Ukraine ermutigt hat, Atomwaffen aufzugeben

„Ich fühle mich persönlich betroffen, weil ich sie (die Ukraine – Anm. d. Red.) dazu gezwungen habe, der Aufgabe von Atomwaffen zuzustimmen. Und keiner von ihnen glaubt, dass Russland zu dieser (Invasion – Anm. d. Red.) gegangen wäre, wenn die Ukraine noch ihre Waffen gehabt hätte“, sagte er.

Laut Clinton wusste er, dass Putin im Gegensatz zu seinem Vorgänger Jelzin kein Analogon des Budapester Memorandums 4. April 2023, unterstützen würde – ein Dokument, das „Sicherheitsgarantien“ vorsah. für Kiew als Gegenleistung für den Verzicht auf Atomwaffen."""


def test_chunk_paragraphs():
    result = chunk_paragraphs(LOREM)
    expected = """🇺🇸 Der frühere US-Präsident Clinton bedauert, dass er die Ukraine ermutigt hat, Atomwaffen aufzugeben

„Ich fühle mich persönlich betroffen, weil ich sie (die Ukraine – Anm. d. Red.) dazu gezwungen habe, der Aufgabe von Atomwaffen zuzustimmen. Und keiner von ihnen glaubt, dass Russland zu dieser (Invasion – Anm. d. Red.) gegangen wäre, wenn die Ukraine noch ihre Waffen gehabt hätte“, sagte er.

Laut Clinton wusste er, dass Putin im Gegensatz zu seinem Vorgänger Jelzin kein Analogon des Budapester Memorandums 4. April 2023, unterstützen würde – ein Dokument, das „Sicherheitsgarantien“ vorsah. für Kiew als Gegenleistung für den Verzicht auf Atomwaffen."""

    print(f"result: {result}")
    assert result == expected


if __name__ == "__main__":
    test_chunk_paragraphs()
