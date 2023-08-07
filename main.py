from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals

import requests
from dotenv import load_dotenv
import os
import nltk
import re

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer as Summarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

LANGUAGE = "english"
SENTENCES_COUNT = 2

nltk.download('punkt')

COMMA_FEED_URL = "http://127.0.0.1:8082/rest/"
COMMA_FEED_API_KEY = "bdee4e0f1ef6a75da23559b055e1847e51adbf22"


def remove_html_tags(input_string):
    clean_text = re.sub('<.*?>', ' ', input_string)
    return clean_text


def summer(content: str) -> str:
    result = ""
    parser = PlaintextParser.from_string(content, Tokenizer(LANGUAGE))
    stemmer = Stemmer(LANGUAGE)

    summarizer = Summarizer(stemmer)
    summarizer.stop_words = get_stop_words(LANGUAGE)

    for sentence in summarizer(parser.document, SENTENCES_COUNT):
        result += str(sentence) + "\n"

    return result



def get_unread_feeds():
    res = requests.get(COMMA_FEED_URL + "category/entries",
                       params={"apiKey": COMMA_FEED_API_KEY, "readType": "unread", "id": "all"})
    resJson = res.json()

    for entre in resJson["entries"]:
        print(entre["url"])
        print(entre["title"])
        print(summer(remove_html_tags(entre["content"])))


if __name__ == "__main__":
    get_unread_feeds()


