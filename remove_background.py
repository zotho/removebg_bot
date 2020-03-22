import os
import os.path
import logging
import urllib.request
import time
from queue import SimpleQueue
from pathlib import Path
from typing import Optional

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    NoAlertPresentException,
    JavascriptException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem

from configs import (
    SERVICE_URL,
    PROXY_HOST,
    PROXY_PORT,
    IMAGE_SERVER_HOST,
    IMAGE_SERVER_PORT,
    IMAGE_SERVER_PROCESSED_FOLDER_PATH,
)
from file_watcher import FileWatcher

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


DROP_FILE_JS_SCRIPT: str = "wd-drop-file.js"


class RemoveBackground:
    service_url: str = SERVICE_URL
    js_script_path: Path = Path(DROP_FILE_JS_SCRIPT)
    js_drop_script: str = js_script_path.read_text()

    def __init__(self, timeout: int = 10):
        """Init selenium web driver."""
        self.start(timeout=timeout)

    def start(self, timeout: int = 10):
        chrome_options = Options()

        software_names = [SoftwareName.CHROME.value]
        operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]

        user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=100)
        user_agent = user_agent_rotator.get_random_user_agent()

        # For future server deploy
        # chrome_options.add_argument("--headless")
        # chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument(f"user-agent={user_agent}")

        host = PROXY_HOST
        port = PROXY_PORT
        proxy = f"{host}:{port}"

        # webdriver.DesiredCapabilities.CHROME["proxy"] = {
        #     "httpProxy":proxy,
        #     # "ftpProxy":proxy,
        #     "sslProxy":proxy,
        #     # "noProxy":None,
        #     "proxyType":"MANUAL",
        #     "class":"org.openqa.selenium.Proxy",
        #     "autodetect":False
        # }

        self.driver = webdriver.Chrome(
            options=chrome_options,
            # desired_capabilities=webdriver.DesiredCapabilities.CHROME
        )
        self.wait = WebDriverWait(self.driver, timeout)

        # Check ip
        # self.driver.get("http://lumtest.com/myip.json")
        # time.sleep(10)
        # raise

        logger.info(f"Getting URL: {self.service_url}")
        self.driver.get(self.service_url)
        # self.dropzone = self.driver.find_element_by_css_selector("#page-content")

        self.element_filter = ElementWithSrcPart(locator="img.transparency-grid", src_part="downloads")

        # Remove proxy ad element
        try:
            self.driver.execute_script("document.getElementById(\"buorg\").remove();")
        except JavascriptException:
            pass

    def process_image(self, image_path: Path, output_path: Optional[Path] = None, timeout: float = 3.0, temp_suffix: str = ".temp"):
        """Process image with timeout."""

        time.sleep(timeout)

        # self.drop_file(self.dropzone, str(image_path.absolute()))
        self.paste_file_url(image_path)

        element = self.wait.until(self.element_filter)
        image_src: str = element.get_attribute("src")

        if not output_path:
            suffix: str = image_path.suffix
            output_name: Path = image_path.with_suffix(".png")
            output_path: Path = Path(IMAGE_SERVER_PROCESSED_FOLDER_PATH) / output_name

        time.sleep(timeout)

        temp_path = output_path.with_suffix(temp_suffix)
        urllib.request.urlretrieve(image_src, str(temp_path))
        os.rename(str(temp_path), str(output_path))

    def paste_file_url(self, image_path):
        """Click to URL button and paste image URL to alert form."""

        url_element = self.driver.find_element_by_link_text("URL")

        # Scroll to page top for URL not be fence
        self.driver.find_element_by_tag_name("body").send_keys(Keys.CONTROL + Keys.HOME)

        self.perform_click(url_element)

        alert = self.driver.switch_to.alert

        alert.send_keys(f"http://{IMAGE_SERVER_HOST}:{IMAGE_SERVER_PORT}/{image_path.name}")
        alert.accept()

    def drop_file(self, element, file, offsetX=0, offsetY=0):
        """Drag and drop file to web element."""

        if not os.path.isfile(file):
            raise FileNotFoundError(file)

        elm_input = self.driver.execute_script(self.js_drop_script, element, offsetX, offsetY)
        elm_input._execute("sendKeysToElement", {"value": [file], "text": file})

    def perform_click(self, element):
        """Move to element and click on it."""
        webdriver.ActionChains(self.driver).move_to_element(element).click(element).perform()

    def close(self):
        self.driver.close()
        del self.driver

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type:
            logger.error(f"Error:: {exc_type}. Text: {exc_value}. Traceback: {exc_traceback}.")
            self.driver.save_screenshot(f"screenshot_{time.strftime('%Y.%m.%d_%H.%M.%S%Z')}.png")
        self.close()

    def restart(self, timeout: int = 10):
        self.close()
        self.start(timeout=timeout)


class ElementWithSrcPart:
    """Element used for WebDriverWait.until function."""

    def __init__(self, locator: str, src_part: str):
        """Init example.

        - locator="img.transparency-grid"
        - src_part="downloads"

        Save `processed_urls` in self.
        """
        self.locator: str = locator
        self.src_part: str = src_part
        self.processed_urls: str = set()

    def __call__(self, driver):
        """Find element by locator.
        Then filtered by `src_part` and not processed yet.
        """
        try:
            elements = driver.find_elements_by_css_selector(self.locator)
        except NoSuchElementException:
            return False

        for element in elements:
            element_src: str = element.get_attribute("src")
            if self.src_part in element_src and element_src not in self.processed_urls:
                self.processed_urls.add(element_src)
                return element
        return False


def main():
    with RemoveBackground(timeout=15) as remove_background:
        for path_str in ("1.jpg", "2.jpg", "3.jpg", "4.jpg"):
            remove_background.process_image(Path(path_str))


def watcher():
    with RemoveBackground(timeout=15) as remove_background:
        queue = SimpleQueue()

        def callback(path):
            path = Path(path)
            if path.suffix in {".jpg", ".jpeg", ".png"}:
                queue.put(path.name)

        watcher = FileWatcher(callback)

        try:
            while True:
                item = queue.get()
                while True:
                    try:
                        remove_background.process_image(Path(item))
                    except TimeoutException:
                        remove_background.close()
                        del remove_background
                        remove_background = RemoveBackground(timeout=15)
                        remove_background.start()
                    else:
                        break
        except KeyboardInterrupt:
            watcher.stop()

if __name__ == "__main__":
    # main()
    watcher()
