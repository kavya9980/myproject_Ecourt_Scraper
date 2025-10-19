
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from twocaptcha import TwoCaptcha
import os
from utils.logger import logger

# 2Captcha API key
CAPTCHA_API_KEY = os.getenv("TWOCAPTCHA_API_KEY", "your_2captcha_api_key")
solver = TwoCaptcha(CAPTCHA_API_KEY) if CAPTCHA_API_KEY != "your_2captcha_api_key" else None

def input_captcha():
    logger.info("Prompting for manual captcha input via console")
    print("Please look at the browser window and enter the captcha code shown:")
    return input().strip()

def solve_captcha(driver, use_2captcha=True):
    if use_2captcha and solver:
        try:
            logger.info("Attempting to solve CAPTCHA with 2Captcha")
            captcha_img = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "captcha_image")))
            captcha_url = captcha_img.get_attribute("src")
            result = solver.normal(captcha_url)
            captcha_code = result['code']
            logger.info("CAPTCHA solved: %s", captcha_code)
            return captcha_code, None
        except Exception as e:
            logger.error("2Captcha failed: %s, falling back to manual input", e)
            return None, str(e)
    return None, "2Captcha not configured or disabled"

def get_captcha_image(driver):
    try:
        captcha_img = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "captcha_image")))
        return captcha_img.get_attribute("src"), None
    except Exception as e:
        logger.error("Failed to get CAPTCHA image: %s", e)
        return None, str(e)

def refresh_captcha(driver):
    try:
        refresh_button = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.ID, "captchaRefresh")))
        refresh_button.click()
        import time
        time.sleep(1)
        return get_captcha_image(driver)
    except Exception as e:
        logger.error("Failed to refresh CAPTCHA: %s", e)
        return None, str(e)
