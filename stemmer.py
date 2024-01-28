import re

__all__ = ("Stemmer",)

# http://uk.wikipedia.org/wiki/Голосний_звук
VOWEL = re.compile(r"аеиоуюяіїє")
PERFECTIVEGROUND = re.compile(
    r"(ив|ивши|ившись|ыв|ывши|ывшись((?<=[ая])(в|вши|вшись)))$"
)
# http://uk.wikipedia.org/wiki/Рефлексивне_дієслово
REFLEXIVE = re.compile(r"(с[яьи])$")
# http://uk.wikipedia.org/wiki/Прикметник + http://wapedia.mobi/uk/Прикметник
ADJECTIVE = re.compile(
    r"(ими|ій|ий|а|е|ова|ове|ів|є|їй|єє|еє|я|ім|ем|им|ім|их|іх|ою|йми|іми|у|ю|ого|ому|ої)$"
)
# http://uk.wikipedia.org/wiki/Дієприкметник
PARTICIPLE = re.compile(r"(ий|ого|ому|им|ім|а|ій|у|ою|ій|і|их|йми|их)$")
# http://uk.wikipedia.org/wiki/Дієслово
VERB = re.compile(r"(сь|ся|ив|ать|ять|у|ю|ав|али|учи|ячи|вши|ши|е|ме|ати|яти|є)$")
# http://uk.wikipedia.org/wiki/Іменник
NOUN = re.compile(
    r"(а|ев|ов|е|ями|ами|еи|и|ей|ой|ий|й|иям|ям|ием|ем|ам|ом|о|у|ах|иях|ях|ы|ь|ию|ью|ю|ия|ья|я|і|ові|ї|ею|єю|ою|є|еві|ем|єм|ів|їв|ю)$"
)
RVRE = re.compile(r"[аеиоуюяіїє]")
DERIVATIONAL = re.compile(
    r"[^аеиоуюяіїє][аеиоуюяіїє]+[^аеиоуюяіїє]+[аеиоуюяіїє].*(?<=о)сть?$"
)

UK_WORDS = re.compile(r"[аеиоуюяіїє]")

cybersport_exceptions = {
    "кіберспортивну",
    "кіберспортивний",
    "кіберспортивних",
    "кіберспортивні",
    "кіберспортивної",
    "кіберспортивною",
    "кіберспортсмени",
    "кіберспортсменам",
    "кіберспортсмена",
    "кіберспортсмен",
    "кіберспортсменів",
    "кіберспортсмену",
}
competitions_exceptions = {"змаганнях", "змагання", "змаганнями", "змаганням"}
uk_exceptions = {
    "українських",
    "український",
    "українському",
    "українські",
    "українського",
    "українська",
}
sport_exceptions = {
    "спортсменів",
    "спортсмени",
    "спортсмен",
    "спортивних",
    "спортивними",
    "спортивної",
    "спортивного",
    "спортивні",
    "спортивним",
}
gaming_exceptions = {
    "ігрової",
    "ігровий",
    "ігрову",
    "ігрового",
    "ігрових",
    "ігор",
    "гри",
}


class Stemmer:
    def __init__(self):
        self.RV = ""

    def __ukstemmer_search_preprocess(self, word):
        word = word.lower()
        word = word.replace("'", "")
        word = word.replace("ё", "е")
        word = word.replace("ъ", "ї")
        return word

    def __s(self, st: str, reg: re.Pattern[str], to: str):
        orig = st
        self.RV = reg.sub(to, st)
        return orig != self.RV

    def __s_raw(self, st: str, reg: str, to: str):
        orig = st
        self.RV = re.sub(reg, to, st)
        return orig != self.RV

    def stem_word(self, word: str) -> str:
        """Find the basis (stem) of a word.
        1. word - source word (UTF-8 encoded string)
        2. returns the stemmed form of the word (UTF-8 encoded string)"""

        word = self.__ukstemmer_search_preprocess(word)

        # exceptions
        if word in cybersport_exceptions:
            return "кіберспорт"

        if word in competitions_exceptions:
            return "змаган"

        if word in uk_exceptions:
            return "україн"

        if word in sport_exceptions:
            return "спорт"

        if word in gaming_exceptions:
            return "ігр"

        if not UK_WORDS.search(word):
            stemma = word
        else:
            p = RVRE.search(word)
            start = word[0 : p.span()[1]]
            self.RV = word[p.span()[1] :]

            # Step 1
            if not self.__s(self.RV, PERFECTIVEGROUND, ""):
                self.__s(self.RV, REFLEXIVE, "")
                if self.__s(self.RV, ADJECTIVE, ""):
                    self.__s(self.RV, PARTICIPLE, "")
                else:
                    if not self.__s(self.RV, VERB, ""):
                        self.__s(self.RV, NOUN, "")
            # Step 2
            self.__s_raw(self.RV, "и$", "")

            # Step 3
            if DERIVATIONAL.search(self.RV):
                self.__s_raw(self.RV, "ость$", "")

            # Step 4
            if self.__s_raw(self.RV, "ь$", ""):
                self.__s_raw(self.RV, "ейше?$", "")
                self.__s_raw(self.RV, "нн$", "н")

            stemma = start + self.RV
        return stemma
