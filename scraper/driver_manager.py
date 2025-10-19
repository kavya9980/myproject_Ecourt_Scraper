
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import os
from utils.logger import logger

def get_driver(download_dir=None):
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36")
    options.add_argument("--disable-blink-features=AutomationControlled")
    if download_dir:
        os.makedirs(download_dir, exist_ok=True)
        options.add_experimental_option("prefs", {"download.default_directory": download_dir})
    service = Service(r"C:\Users\chromedriver.exe")
    logger.debug("Initializing WebDriver")
    return webdriver.Chrome(service=service, options=options)
