import os
import logging
import uuid
from pathlib import Path
from functools import partial

import telegram
from telegram.ext import (
    Filters,
    MessageHandler,
    Updater,
)

from configs import (
    IMAGE_SERVER_TEMP_PATH,
    IMAGE_SERVER_FOLDER_PATH,
    IMAGE_SERVER_PROCESSED_FOLDER_PATH,
    TG_TOKEN,
)
from file_watcher import FileWatcher


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


TEMP_FOLDER_PATH = Path(IMAGE_SERVER_TEMP_PATH)
FOLDER_PATH = Path(IMAGE_SERVER_FOLDER_PATH)
PROCESSED_PATH = Path(IMAGE_SERVER_PROCESSED_FOLDER_PATH)

name_callback_mapping = dict()

def extract_name(filename: str) -> str:
    """Remove suffix."""
    return str(Path(filename).with_suffix(""))

def answer_result(update, context, image_name):
    image_path = PROCESSED_PATH / image_name
    update.message.reply_photo(image_path.open("rb"))

def image_handler(update, context):
    photos = update.message.photo
    saved_file = None

    for photo in photos:
        file = photo.get_file()
        if not saved_file or file.file_size > saved_file.file_size:
            saved_file = file

    pure_name = uuid.uuid4().hex
    new_name = f"{pure_name}.jpg"
    temp_path = str(TEMP_FOLDER_PATH / new_name)
    imgs_path = str(FOLDER_PATH / new_name)

    name_callback_mapping[pure_name] = partial(answer_result, update, context)

    saved_file.download(temp_path)

    os.replace(temp_path, imgs_path)

def error_handler(update, context):
    logger.error("Error!")

def handle_file_processed(path):
    path = Path(path)
    if path.suffix not in {".png"}:
        return
    filename = path.name
    callback = name_callback_mapping.pop(extract_name(filename))
    callback(filename)

def main():
    updater = Updater(TG_TOKEN, use_context=True)

    handler = MessageHandler(Filters.photo, image_handler)

    watcher = FileWatcher(handle_file_processed, path=IMAGE_SERVER_PROCESSED_FOLDER_PATH)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(handler)
    dispatcher.add_error_handler(error_handler)

    updater.start_polling()
    updater.idle()

    # Stopping
    watcher.stop()


if __name__ == '__main__':
    main()
