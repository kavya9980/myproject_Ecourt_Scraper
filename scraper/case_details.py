
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from bs4 import BeautifulSoup
import time
from utils.logger import logger
from scraper.captcha_solver import get_captcha_image

def get_case_details(driver, args, captcha_code=None, retries=3):
    for attempt in range(retries):
        try:
            logger.info(f"Attempt {attempt + 1}: Navigating to eCourts")
            driver.get("https://services.ecourts.gov.in/ecourtindia_v6/")
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            logger.info("Page body loaded")

            # Get CAPTCHA image URL
            captcha_url, captcha_error = get_captcha_image(driver)
            if captcha_error:
                return None, captcha_error, captcha_url

            if args.cnr:
                if not args.cnr.strip():
                    logger.error("CNR is empty")
                    return None, "Error: CNR is empty", captcha_url
                try:
                    logger.info("Locating CNR input")
                    try:
                        cnr_input = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "cino")))
                    except NoSuchElementException:
                        logger.warning("Primary CNR input (cino) not found, trying alternative")
                        cnr_input = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='cino']")))
                    cnr_input.send_keys(args.cnr)
                    logger.info("Locating captcha input")
                    captcha_input = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "fcaptcha_code")))
                    if captcha_code:
                        logger.info("Using user-entered CAPTCHA code")
                        captcha_input.send_keys(captcha_code)
                    else:
                        from scraper.captcha_solver import solve_captcha
                        captcha, captcha_error = solve_captcha(driver, use_2captcha=True)
                        if captcha_error and not captcha:
                            return None, captcha_error, captcha_url
                        captcha_input.send_keys(captcha)
                    logger.info("Locating search button")
                    search_button = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.ID, "searchbtn")))
                    search_button.click()
                    logger.info("Waiting for case details table")
                    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, "case_details_table")))
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    table = soup.find('table', class_='case_details_table')
                    if not table:
                        logger.error("Case not found or invalid captcha")
                        return None, "Case not found or invalid captcha", captcha_url
                    details = {}
                    for tr in table.find_all('tr'):
                        tds = tr.find_all('td')
                        if len(tds) == 2:
                            key = tds[0].text.strip().replace(':', '')
                            value = tds[1].text.strip()
                            details[key] = value
                    logger.info("Case details retrieved successfully")
                    return {
                        'state': details.get('State', args.state if hasattr(args, 'state') else ''),
                        'district': details.get('District', ''),
                        'court': details.get('Court Establishment', ''),
                        'next_hearing': details.get('Next Hearing Date', ''),
                        'case_number': details.get('Registration Number', args.cnr),
                        'court_number': details.get('Court Number', ''),
                        'status': details.get('Case Status', '')
                    }, None, captcha_url
                except (TimeoutException, NoSuchElementException) as e:
                    logger.error(f"Attempt {attempt + 1} failed: {e}")
                    driver.save_screenshot(f"error_screenshot_{attempt + 1}.png")
                    with open(f"error_page_{attempt + 1}.html", "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                    if attempt < retries - 1:
                        time.sleep(2)
                        continue
                    return None, f"Failed to fetch case details: {e}", captcha_url
            else:
                if not all([args.state, args.district, args.court, args.case_type, args.case_number, args.year]):
                    logger.error("Missing required fields for case type query")
                    return None, "Error: Missing required fields (state, district, court, case_type, case_number, year)", captcha_url
                driver.get("https://services.ecourts.gov.in/ecourtindia_v6/?p=casestatus/index")
                try:
                    logger.info("Locating state dropdown")
                    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "court_state_code")))
                    Select(driver.find_element(By.ID, "court_state_code")).select_by_visible_text(args.state)
                    time.sleep(1)
                    logger.info("Locating district dropdown")
                    Select(driver.find_element(By.ID, "court_dist_code")).select_by_visible_text(args.district)
                    time.sleep(1)
                    logger.info("Locating court dropdown")
                    Select(driver.find_element(By.ID, "court_complex_code")).select_by_visible_text(args.court)
                    time.sleep(1)
                    logger.info("Locating case type dropdown")
                    Select(driver.find_element(By.ID, "case_type")).select_by_visible_text(args.case_type)
                    driver.find_element(By.ID, "case_no").send_keys(args.case_number)
                    Select(driver.find_element(By.ID, "case_yr")).select_by_value(args.year)
                    if captcha_code:
                        logger.info("Using user-entered CAPTCHA code")
                        driver.find_element(By.ID, "fcaptcha_code").send_keys(captcha_code)
                    else:
                        from scraper.captcha_solver import solve_captcha
                        captcha, captcha_error = solve_captcha(driver, use_2captcha=True)
                        if captcha_error and not captcha:
                            return None, captcha_error, captcha_url
                        driver.find_element(By.ID, "fcaptcha_code").send_keys(captcha)
                    driver.find_element(By.ID, "search_reg_btn").click()
                    logger.info("Waiting for case details table")
                    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, "case_details_table")))
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    table = soup.find('table', class_='case_details_table')
                    if not table:
                        logger.error("Case not found or invalid captcha")
                        return None, "Case not found or invalid captcha", captcha_url
                    details = {}
                    for tr in table.find_all('tr'):
                        tds = tr.find_all('td')
                        if len(tds) == 2:
                            key = tds[0].text.strip().replace(':', '')
                            value = tds[1].text.strip()
                            details[key] = value
                    logger.info("Case details retrieved successfully")
                    return {
                        'state': args.state,
                        'district': args.district,
                        'court': args.court,
                        'next_hearing': details.get('Next Hearing Date', ''),
                        'case_number': f"{args.case_type}/{args.case_number}/{args.year}",
                        'court_number': details.get('Court Number', ''),
                        'status': details.get('Case Status', '')
                    }, None, captcha_url
                except (TimeoutException, NoSuchElementException) as e:
                    logger.error(f"Attempt {attempt + 1} failed: {e}")
                    driver.save_screenshot(f"error_screenshot_{attempt + 1}.png")
                    with open(f"error_page_{attempt + 1}.html", "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                    if attempt < retries - 1:
                        time.sleep(2)
                        continue
                    return None, f"Failed to fetch case details: {e}", captcha_url
        except WebDriverException as e:
            logger.error(f"Attempt {attempt + 1} failed with WebDriverException: {e}")
            driver.save_screenshot(f"error_screenshot_{attempt + 1}.png")
            with open(f"error_page_{attempt + 1}.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            if attempt < retries - 1:
                time.sleep(2)
                continue
            return None, f"WebDriverException: {e}", captcha_url
        except Exception as e:
            logger.error(f"Unexpected error in get_case_details: {e}")
            driver.save_screenshot(f"error_screenshot_{attempt + 1}.png")
            with open(f"error_page_{attempt + 1}.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            return None, f"Unexpected error: {e}", captcha_url
