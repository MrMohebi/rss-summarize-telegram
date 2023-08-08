from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals

import requests
from dotenv import load_dotenv
import os
import nltk
import re
from pathlib import Path

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer as Summarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words
import configparser

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, filters, MessageHandler

load_dotenv()

LANGUAGE = "english"
SENTENCES_COUNT = 2

nltk.download('punkt')

COMMA_FEED_URL = "http://127.0.0.1:8082/rest/"


class AuthCommaFeed:
    username: str
    password: str

    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password

    def to_set(self):
        return tuple([self.username, self.password])

    def is_valid(self):
        return self.password is not None and self.username is not None


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


def get_unread_feeds(auth: AuthCommaFeed) -> list[dict]:
    result = []
    res = requests.get(COMMA_FEED_URL + "category/entries",
                       params={"readType": "unread", "id": "all"}, auth=auth.to_set())

    if res.status_code != 200:
        return []

    resJson = res.json()

    for entre in resJson["entries"]:
        result.append({
            "id": entre["id"],
            "url": entre["url"],
            "title": entre["title"],
            "content_sum": summer(remove_html_tags(entre["content"])),
        })

    return result


def mark_feed_read(id: int, auth: AuthCommaFeed) -> bool:
    try:
        res = requests.post(COMMA_FEED_URL + "entry/mark", auth=auth.to_set(),
                            json={"read": True, "id": str(id)})
        return True
    except Exception as e:
        print(e)
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Please choose:")


async def set_auth_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global config

    if len(update.message.text.split(" ")) != 3:
        await update.message.reply_text("Please send commaFeed auth as fallowing: \n/set_auth <USERNAME> <PASSWORD>",
                                        reply_markup=ReplyKeyboardRemove())
        return

    username = update.message.text.split(" ")[1]
    password = update.message.text.split(" ")[2]

    save_auth_data_config(update.message.chat.id, username, password)

    keyboard = [
        [KeyboardButton("Get unread feeds")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "bot activated with fallowing auth:\nusername: {}\npassword: {} ".format(username, password),
        reply_markup=reply_markup)


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global config
    if update.message.text == "Get unread feeds":
        auth = AuthCommaFeed(config.get(str(update.message.chat.id), "username", fallback=None),
                             config.get(str(update.message.chat.id), "password", fallback=None))

        if not auth.is_valid():
            await update.message.reply_text(
                "Please send commaFeed auth as fallowing: \n/set_auth <USERNAME> <PASSWORD>",
                reply_markup=ReplyKeyboardRemove())
            return

        feeds = get_unread_feeds(auth)

        if len(feeds) < 1:
            await update.message.reply_text("there is no unread feed OR ur api_key is invalid!")
            return

        await update.message.reply_text("<-------start------->")
        for feed in feeds:
            result = ""
            result += feed["title"] + "\n\n"
            result += feed["content_sum"] + "\n\n"
            result += feed["url"]
            await update.message.reply_text(result)
            mark_feed_read(feed["id"], auth)

        await update.message.reply_text("<--------end-------->")


def main() -> None:
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    TELEGRAM_PROXY = os.getenv('TELEGRAM_PROXY')
    print(TELEGRAM_PROXY)
    application = Application.builder().token(TELEGRAM_TOKEN).proxy_url(TELEGRAM_PROXY).get_updates_proxy_url(
        TELEGRAM_PROXY).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set_auth", set_auth_command))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


def save_config():
    global configFilePath, config
    config.write(configFilePath.open("w"))


def save_auth_data_config(id: int, username: str, password: str):
    global config
    try:
        config.get(str(id), username)
    except configparser.NoSectionError:
        config.add_section(str(id))
    config.set(str(id), "username", username)
    config.set(str(id), "password", password)

    save_config()


if __name__ == "__main__":
    configFilePath = Path('./configs/config.ini')
    if not configFilePath.exists():
        configFilePath.parent.mkdir(parents=True, exist_ok=True)
        with configFilePath.open('w') as config_file:
            config_file.write("")

    config = configparser.ConfigParser()
    config.read(configFilePath)

    main()
