import os
import re
import abc
import stemmer

from collections import Counter

NON_NUMERIC_PATTERN = re.compile(r"[^a-zA-Zа-яА-ЯіІюЮєЄїЇ ]+")


class AbstractParagraph(abc.ABC):
    id: int
    text: str
    original: str

    def __init__(self, idx: int, text: str, original: str) -> None:
        self.id = idx
        self.text: str = text
        self.original = original

    def __str__(self) -> str:
        return f"Paragraph №{self.id}.\nProcessed text:\n\r\r{self.text}\nOriginal text:\n\r\r{self.original}"

    def __repr__(self) -> str:
        return self.__str__()


class Paragraph(AbstractParagraph):
    def __init__(self, idx: int, text: str, original: str):
        super().__init__(idx, text, original)


class ParagraphWithoutStopWords(AbstractParagraph):
    stopwords: set[str]

    def __init__(self, idx: int, text: str, original: str, stopwords: set[str]):
        super().__init__(idx, text, original)
        self.stopwords = stopwords

    def __str__(self) -> str:
        return f"Paragraph №{self.id}.\nProcessed text:\n\r\r{self.text}\nStopWords:\n\r\r{self.stopwords}\nOriginal text:\n\r\r{self.original}."

    @classmethod
    def from_paragraph(
        cls, paragraph: Paragraph, stopwords: set[str]
    ) -> "ParagraphWithoutStopWords":
        removed_stopwords = []
        swords = set()
        for word in paragraph.text.split():
            if word in stopwords:
                swords.add(word)
            else:
                removed_stopwords.append(word)

        return cls(
            paragraph.id, " ".join(removed_stopwords), paragraph.original, swords
        )


class StemmedParagraph(ParagraphWithoutStopWords):
    stemmed: dict[str, set[str]]
    word_count: int

    def __init__(
        self,
        idx: int,
        text: str,
        original: str,
        stopwords: set[str],
        stemmed: dict[str, set[str]],
    ):
        super().__init__(idx, text, original, stopwords)
        self.stemmed = stemmed
        self.word_count = len(text.split())

    def extract_keywords(
        self, top_n: int = 25, fmt=False
    ) -> list[tuple[str, int]] | list[str]:
        if fmt:
            return [
                (f"{keyword}: ({', '.join(self.stemmed[keyword])})", frequency)
                for (keyword, frequency) in Counter(self.text.split()).most_common(
                    top_n
                )
            ]
        return [
            keyword for (keyword, _) in Counter(self.text.split()).most_common(top_n)
        ]

    def __str__(self) -> str:
        return f"""
            * Paragraph №{self.id}.\n
            * Processed text:\n
            * \r\r{self.text}\n
            * StopWords:\n
            * \r\r{self.stopwords}\n
            * Stemmed words: {self.fmt_stem()}\n
            * Original text:\n
            * \r\r{self.original}.
        """

    def fmt_stem(self) -> str:
        return [
            f"{key}({', '.join(value)})" if len(value) > 1 else f"{key}"
            for (key, value) in self.stemmed.items()
        ]

    @classmethod
    def from_paragraph_without_stopwords(
        cls, paragraph: ParagraphWithoutStopWords
    ) -> "StemmedParagraph":
        stemmed_words: dict[str, set[str]] = {}
        stemmed_text = []

        for word in paragraph.text.split():
            stem = stemmer.Stemmer()
            stemmed_word = stem.stem_word(word)
            stemmed_text.append(stemmed_word)

            if (stems := stemmed_words.get(stemmed_word)) is not None:
                stems.add(word)
            else:
                stemmed_words[stemmed_word] = set([word])

        return cls(
            paragraph.id,
            " ".join(stemmed_text),
            paragraph.original,
            paragraph.stopwords,
            stemmed_words,
        )


class Aggregator:
    paragraphs: list[StemmedParagraph]
    keywords: list[str]

    def __init__(self, paragraphs: list[StemmedParagraph], keywords: list[str]) -> None:
        self.paragraphs = paragraphs
        self.keywords = keywords

    def calculate_frequency_for_keyword(self, keyword: str) -> list[float]:
        return [
            p.text.split().count(keyword) / float(p.word_count) for p in self.paragraphs
        ]

    def make_xslx_document(self) -> None:
        import pandas as pd
        import math

        data = {
            "Номер абзацу": [n.id for n in self.paragraphs],
            "Кіл-сть слів в абзаці": [n.word_count for n in self.paragraphs],
            "Евклідова відстань": [],
        }

        avg_frequency = {}
        ev_distance: list[float] = [0.0 for _ in range(len(self.paragraphs))]

        for keyword in self.keywords:
            frequency = self.calculate_frequency_for_keyword(keyword)
            avg_frequency[keyword] = sum(frequency) / len(frequency)

            for idx, freq in enumerate(frequency):
                ev_distance[idx] += (avg_frequency[keyword] - freq) ** 2
            data[keyword.capitalize()] = frequency

        for f in ev_distance:
            f = math.sqrt(f)

        data["Евклідова відстань"] = ev_distance

        variance = sum(map(lambda x: x**2, ev_distance)) / len(ev_distance)
        sigma = math.sqrt(variance)

        print(sigma, 2 * sigma, 3 * sigma)

        sigmas_paragraph = {"S": [], "2S": [], "3S": [], ">3S": []}
        for idx, v in enumerate(ev_distance):
            if v <= sigma:
                sigmas_paragraph["S"].append(idx)
            elif sigma < v <= 2 * sigma:
                sigmas_paragraph["2S"].append(idx)
            elif 2 * sigma < v <= 3 * sigma:
                sigmas_paragraph["3S"].append(idx)
            else:
                sigmas_paragraph[">3S"].append(idx)

        print(sigmas_paragraph)
                
        for v in sigmas_paragraph["S"]:
            print(self.paragraphs[v].original)

        df = pd.DataFrame(
            data=data,
        )

        df.to_excel("kr.xlsx",
             sheet_name='Sheet_name_1')


def load_data(path: str) -> list[str]:
    with open(path, "r") as file:
        return [item for item in file.readlines()]


def preprocess_data(data: list[str]) -> list[str]:
    return [NON_NUMERIC_PATTERN.sub("", item.strip().lower()) for item in data]


def make_paragraph(data: list[str]) -> list[Paragraph]:
    return [
        Paragraph(idx, item, original)
        for (idx, (item, original)) in enumerate(
            zip(preprocess_data(data[::]), data), start=1
        )
        if item
    ]


def remove_stopwords(
    paragraphs: list[Paragraph], stopwords: set[str]
) -> list[ParagraphWithoutStopWords]:
    return [
        ParagraphWithoutStopWords.from_paragraph(item, stopwords) for item in paragraphs
    ]


def stem_words(
    paragraphs: list[ParagraphWithoutStopWords],
) -> list[StemmedParagraph]:
    return [
        StemmedParagraph.from_paragraph_without_stopwords(item) for item in paragraphs
    ]


def load_stopwords(path: str) -> set[str]:
    with open(path, "r") as file:
        return set([item.strip() for item in file.readlines()])


def main():
    stopwords = preprocess_data(
        load_stopwords(os.path.join(os.getcwd(), "data", "stopwords.txt"))
    )
    full_text = stem_words(
        remove_stopwords(
            make_paragraph(
                ["\n".join(load_data(os.path.join(os.getcwd(), "data", "text.txt")))]
            ),
            stopwords,
        )
    )[0]
    print(
        "\n".join(
            [
                f"{idx}: {word} - Frequency: {frequency}."
                for (idx, (word, frequency)) in enumerate(
                    full_text.extract_keywords(fmt=True)
                )
            ]
        )
    )

    data = make_paragraph(load_data(os.path.join(os.getcwd(), "data", "text.txt")))
    data = remove_stopwords(data, stopwords)
    paragraphs = stem_words(data)

    aggregator = Aggregator(paragraphs, full_text.extract_keywords())
    aggregator.make_xslx_document()


if __name__ == "__main__":
    main()
