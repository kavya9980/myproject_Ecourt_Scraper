
import argparse
from scraper.driver_manager import get_driver
from scraper.case_details import get_case_details
from scraper.cause_list import fetch_cause_list, parse_cause_list
from scraper.captcha_solver import solve_captcha
from utils.logger import logger
from utils.date_utils import get_date_str
from webapp import create_app
import os
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def main():
    parser = argparse.ArgumentParser(description="eCourts Scraper")
    parser.add_argument('--cnr', type=str, help="Case Number (CNR)")
    parser.add_argument('--case_type', type=str, help="Case Type (e.g., WP)")
    parser.add_argument('--case_number', type=str, help="Case Number")
    parser.add_argument('--year', type=str, help="Case Year")
    parser.add_argument('--state', type=str, help="State (e.g., Gujarat)")
    parser.add_argument('--district', type=str, help="District (e.g., Ahmedabad)")
    parser.add_argument('--court', type=str, help="Court (e.g., High Court of Gujarat)")
    parser.add_argument('--today', action='store_true', help="Check today's cause list")
    parser.add_argument('--tomorrow', action='store_true', help="Check tomorrow's cause list")
    parser.add_argument('--causelist', action='store_true', help="Download cause list")
    parser.add_argument('--download_pdf', action='store_true', help="Download case PDF")
    parser.add_argument('--web', action='store_true', help="Run web interface")
    parser.add_argument('--port', type=int, default=8000, help="Port for web server")
    args = parser.parse_args()

    if args.web:
        logger.info(f"Starting Flask server on port {args.port}")
        app = create_app()
        app.run(debug=True, port=args.port)
        return

    if args.causelist:
        if not (args.state and args.district and args.court):
            logger.error("Provide --state --district --court for causelist")
            print("Provide --state --district --court for causelist")
            return
        driver = get_driver()
        try:
            date_str = get_date_str(0)
            pdf_path, error, _ = fetch_cause_list(driver, args.state, args.district, args.court, date_str, os.path.abspath("downloads"))
            if error:
                print(error)
            if pdf_path:
                logger.info(f"Cause list downloaded to {pdf_path}")
                print("Cause list downloaded to", pdf_path)
                with open("result.json", "w") as f:
                    json.dump({"causelist_path": pdf_path}, f, indent=4)
        finally:
            driver.quit()
    else:
        if not (args.cnr or (args.case_type and args.case_number and args.year)):
            logger.error("Provide CNR or Case Type/Number/Year")
            print("Provide CNR or Case Type/Number/Year")
            return
        driver = get_driver()
        try:
            results, _ = run_scraper(args, driver)
            print("\n".join(results['output']))
            if results['errors']:
                print("Errors:", "\n".join(results['errors']))
        finally:
            driver.quit()

def run_scraper(args, driver):
    results = {'output': [], 'errors': []}
    captcha_code = getattr(args, 'captcha_code', None)
    case_details, error, _ = get_case_details(driver, args, captcha_code)
    if error:
        results['errors'].append(error)
        with open("result.json", "w") as f:
            json.dump(results, f, indent=4)
        return results, None
    if not case_details:
        results['errors'].append("Failed to retrieve case details")
        with open("result.json", "w") as f:
            json.dump(results, f, indent=4)
        return results, None
    if case_details['status'] == 'Disposed':
        results['output'].append("Case is disposed, not listed")
        with open("result.json", "w") as f:
            json.dump(results, f, indent=4)
        return results, None
    next_hearing = case_details['next_hearing']
    if not next_hearing:
        results['output'].append("No next hearing date")
        with open("result.json", "w") as f:
            json.dump(results, f, indent=4)
        return results, None
    try:
        from datetime import datetime
        hearing_date = datetime.strptime(next_hearing, '%d-%m-%Y')
    except:
        results['errors'].append("Invalid date format")
        with open("result.json", "w") as f:
            json.dump(results, f, indent=4)
        return results, None
    shifts = []
    if args.today:
        shifts.append(0)
    if args.tomorrow:
        shifts.append(1)
    download_dir = os.path.abspath("downloads")
    os.makedirs(download_dir, exist_ok=True)
    for shift in shifts:
        date_str = get_date_str(shift)
        check_date = datetime.strptime(date_str, '%d-%m-%Y')
        if hearing_date == check_date:
            results['output'].append(f"Case may be listed on {date_str}. Fetching cause list...")
            pdf_path, error, _ = fetch_cause_list(driver, case_details['state'], case_details['district'], case_details['court'], date_str, download_dir, captcha_code)
            if error:
                results['errors'].append(error)
                continue
            if pdf_path:
                serial, court_name, error = parse_cause_list(pdf_path, case_details['case_number'])
                if error:
                    results['errors'].append(error)
                if serial:
                    results['output'].append(f"Serial Number: {serial}")
                    results['output'].append(f"Court Name: {case_details['court_number']}")
                    results[date_str] = {'listed': True, 'serial': serial, 'court': case_details['court_number']}
                else:
                    results['output'].append("Case not found in cause list")
                    results[date_str] = {'listed': False}
                with open("causelist.txt", "w") as f:
                    from pypdf import PdfReader
                    reader = PdfReader(pdf_path)
                    text = ''
                    for page in reader.pages:
                        text += page.extract_text() + '\n'
                    f.write(text)
                if args.download_pdf:
                    try:
                        driver.find_element(By.LINK_TEXT, "Orders").click()
                        import time
                        time.sleep(3)
                        order_link = driver.find_element(By.PARTIAL_LINK_TEXT, "PDF")
                        order_link.click()
                        time.sleep(5)
                        results['output'].append("Case PDF downloaded")
                    except:
                        results['output'].append("No case PDF available")
            else:
                results[date_str] = {'listed': False}
        else:
            results['output'].append(f"Case not listed on {date_str} (next hearing: {next_hearing})")
            results[date_str] = {'listed': False}
    with open("result.json", "w") as f:
        json.dump(results, f, indent=4)
    return results, None

if __name__ == "__main__":
    main()
