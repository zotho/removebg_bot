import time
import logging
from pathlib import Path
from threading import Timer
from functools import partial

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from configs import IMAGE_SERVER_FOLDER_PATH

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def debounce(wait):
    """
    Decorator that will postpone a functions
    execution until after wait seconds
    have elapsed since the last time it was invoked.
    """
    def decorator(function):
        def debounced(*args, **kwargs):
            def call_it():
                function(*args, **kwargs)
            try:
                debounced._timer.cancel()
            except AttributeError:
                pass
            debounced._timer = Timer(wait, call_it)
            debounced._timer.start()
        return debounced
    return decorator


def debounced_handle(path, event_type, callback):
    logger.info(f"Debounced handle process file: {path}. Type: {event_type}.")
    if callback:
        callback(path)


class EventHandler(FileSystemEventHandler):
    callback = None
    argument_partial_mapping = dict()

    def on_moved(self, event):
        self.handle(event.dest_path, "on_moved")

    def on_modified(self, event):
        self.handle(event.src_path, "on_modified")

    def on_created(self, event):
        self.handle(event.src_path, "on_created")

    def handle(self, *args):
        path, event_type = args
        inner_handle = self.argument_partial_mapping.get(args)
        if inner_handle is None:
            @debounce(1)
            def inner_handle():
                debounced_handle(path, event_type, self.callback)
            self.argument_partial_mapping[args] = inner_handle
        inner_handle()


class FileWatcher:
    def __init__(self, callback, path=None):
        event_handler = EventHandler()
        event_handler.callback = callback
        self.observer = Observer()

        path = path or IMAGE_SERVER_FOLDER_PATH
        logger.info(f"Start watching on path {path}")
        self.observer.schedule(event_handler, path, recursive=True)
        self.observer.start()

    def stop(self):
        self.observer.stop()
        self.observer.join()


if __name__ == "__main__":
    watcher = FileWatcher(None)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        watcher.stop()
