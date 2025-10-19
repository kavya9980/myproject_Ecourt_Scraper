
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from utils.logger import logger
from scraper.captcha_solver import get_captcha_image, solve_captcha
from scraper.parser import parse_pdf
import time
import os

def fetch_cause_list(driver, state, district, court, date_str, download_dir, captcha_code=None, retries=3):
    for attempt in range(retries):
        try:
            logger.info(f"Attempt {attempt + 1}: Fetching cause list for {date_str}")
            driver.get("https://services.ecourts.gov.in/ecourtindia_v6/?p=cause_list/index")
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "court_state_code")))
            captcha_url, captcha_error = get_captcha_image(driver)
            if captcha_error:
                return None, captcha_error, captcha_url
            Select(driver.find_element(By.ID, "court_state_code")).select_by_visible_text(state)
            time.sleep(1)
            Select(driver.find_element(By.ID, "court_dist_code")).select_by_visible_text(district)
            time.sleep(1)
            Select(driver.find_element(By.ID, "court_complex_code")).select_by_visible_text(court)
            time.sleep(1)
            driver.find_element(By.ID, "cause_date").send_keys(date_str)
            if captcha_code:
                logger.info("Using user-entered CAPTCHA code")
                driver.find_element(By.ID, "fcaptcha_code").send_keys(captcha_code)
            else:
                captcha, captcha_error = solve_captcha(driver, use_2captcha=True)
                if captcha_error and not captcha:
                    return None, captcha_error, captcha_url
                driver.find_element(By.ID, "fcaptcha_code").send_keys(captcha)
            driver.find_element(By.ID, "search_cl_btn").click()
            time.sleep(3)
            pdf_link = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "View Cause List")))
            pdf_link.click()
            time.sleep(5)
            files = [f for f in os.listdir(download_dir) if f.endswith('.pdf')]
            if files:
                pdf_path = os.path.join(download_dir, max(files, key=os.path.getctime))
                logger.info(f"Cause list downloaded to {pdf_path}")
                return pdf_path, None, captcha_url
            else:
                logger.error("No PDF downloaded")
                return None, "No PDF downloaded", captcha_url
        except (TimeoutException, NoSuchElementException) as e:
            logger.error(f"Attempt {attempt + 1} failed in fetch_cause_list: {e}")
            driver.save_screenshot(f"error_screenshot_cl_{attempt + 1}.png")
            with open(f"error_page_cl_{attempt + 1}.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            if attempt < retries - 1:
                time.sleep(2)
                continue
            return None, f"Failed to fetch cause list: {e}", captcha_url
        except WebDriverException as e:
            logger.error(f"Attempt {attempt + 1} failed with WebDriverException: {e}")
            driver.save_screenshot(f"error_screenshot_cl_{attempt + 1}.png")
            with open(f"error_page_cl_{attempt + 1}.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            if attempt < retries - 1:
                time.sleep(2)
                continue
            return None, f"WebDriverException: {e}", captcha_url
        except Exception as e:
            logger.error(f"Unexpected error in fetch_cause_list: {e}")
            driver.save_screenshot(f"error_screenshot_cl_{attempt + 1}.png")
            with open(f"error_page_cl_{attempt + 1}.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            return None, f"Unexpected error: {e}", captcha_url

def parse_cause_list(file_path, case_number):
    return parse_pdf(file_path, case_number)