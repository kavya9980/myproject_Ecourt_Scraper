# Ecourt_Scraper
The eCourts Scraper is a Python-based web application designed to automate the retrieval of case details and cause lists from the eCourts website.
eCourts Scraper
A Flask-based web application to scrape case details and cause lists from the Indian eCourts portal (https://services.ecourts.gov.in). It supports searching by CNR or Case Type/Number/Year, downloading cause lists, and retrieving case PDFs, with dynamic state, district, and court dropdowns and CAPTCHA verification.
Features

Case Status Tracking: Fetch case details using CNR or Case Type/Number/Year.
Cause List Download: Download cause lists as PDFs and extract text to causelist.txt.
Dynamic Dropdowns: Select from 36 states/UTs, comprehensive districts, and courts (High Courts + district courts).
CAPTCHA Handling: Displays CAPTCHA on initial load and supports manual or 2Captcha-based solving.
Outputs: Saves results to result.json, cause lists to causelist.txt, and PDFs to downloads/.
Web Interface: User-friendly form with validation and responsive design.

Directory Structure
ecourt_scraper/
├── app.py                  # Main Flask application
├── scraper/                # Scraper modules
│   ├── __init__.py
│   ├── driver_manager.py   # Selenium WebDriver setup
│   ├── case_details.py     # Case details scraping
│   ├── cause_list.py       # Cause list downloading
│   ├── captcha_solver.py   # CAPTCHA handling
│   └── parser.py           # PDF parsing
├── webapp/                 # Web interface modules
│   ├── __init__.py
│   ├── routes.py           # Flask routes
│   └── templates/
│       └── index.html      # Web form with dynamic dropdowns
├── utils/                  # Utility modules
│   ├── __init__.py
│   ├── logger.py           # Logging setup
│   └── date_utils.py       # Date handling
├── downloads/              # Output directory for PDFs
├── static/                 # Static assets (e.g., favicon.ico)
├── requirements.txt        # Python dependencies
├── README.md               # This file

Prerequisites

Python: 3.13+
Google Chrome: Latest version
ChromeDriver: Version 141.0.7390.76, placed at E:\Downloads\chromedriver-win32\chromedriver-win32\chromedriver.exe
2Captcha API Key (optional, for automatic CAPTCHA solving)

Setup

Clone Repository:
git clone <your-repo-url>
cd ecourt_scraper


Create Directories:
mkdir downloads
mkdir static
mkdir webapp\templates


Install Dependencies:
pip install -r requirements.txt

Contents of requirements.txt:
selenium==4.25.0
beautifulsoup4==4.12.3
pypdf==5.0.1
flask==3.0.3
2captcha-python==1.5.1


Set Up ChromeDriver:

Download ChromeDriver (version 141.0.7390.76) from https://chromedriver.chromium.org/downloads.
Place at E:\Downloads\chromedriver-win32\chromedriver-win32\chromedriver.exe.


Configure 2Captcha (Optional):

Update scraper/captcha_solver.py:CAPTCHA_API_KEY = "your_2captcha_api_key"


Or set environment variable:setx TWOCAPTCHA_API_KEY "your_2captcha_api_key"


For manual CAPTCHA, set:solver = None





Usage
Web Interface

Run Application:python app.py --web --port 8000


Access:
Open http://127.0.0.1:8000/ in a browser.
CAPTCHA image loads on initial page.
Select state (e.g., Gujarat), district (e.g., Ahmedabad), and court (e.g., Gujarat High Court) from dropdowns.
Enter CNR (e.g., GJHC240000012025) or Case Type/Number/Year (e.g., WP, 12345, 2025).
Enter CAPTCHA code.
Check options (Today, Tomorrow, Cause List, Download PDF).
Click "Search Case Information".


Outputs:
Results displayed in browser.
result.json: Case details.
causelist.txt: Cause list text.
downloads/: PDFs (e.g., causelist_14-10-2025.pdf).



Command Line
python app.py --case_type "WP" --case_number "12345" --year "2025" --state "Gujarat" --district "Ahmedabad" --court "Gujarat High Court" --today --causelist


Outputs same as web interface.

Example
Web Input

State: Gujarat
District: Ahmedabad
Court: Gujarat High Court
Case Type: WP
Case Number: 12345
Year: 2025
Check Today: ✓
Download Cause List: ✓
CAPTCHA: Enter code (e.g., uevhmb)

Expected Output

Browser:Case Details Found
- Case may be listed on 14-10-2025. Fetching cause list...
- Serial Number: 5
- Court Name: Court No. 3


Console:2025-10-14 18:30:00,000 - INFO - Starting Flask server on port 8000
2025-10-14 18:30:02,000 - INFO - Received POST request
2025-10-14 18:30:04,000 - INFO - Attempt 1: Navigating to eCourts
2025-10-14 18:30:06,000 - INFO - Page body loaded
2025-10-14 18:30:07,000 - INFO - Using user-entered CAPTCHA code
2025-10-14 18:30:08,000 - INFO - Case details retrieved successfully


Files:
result.json:{
  "output": [
    "Case may be listed on 14-10-2025. Fetching cause list...",
    "Serial Number: 5",
    "Court Name: Court No. 3"
  ],
  "errors": [],
  "14-10-2025": {
    "listed": true,
    "serial": "5",
    "court": "Court No. 3"
  }
}


causelist.txt: Cause list text.
downloads\causelist_14-10-2025.pdf: Cause list PDF.



Troubleshooting

CAPTCHA Not Showing:
Check error_page_*.html and error_screenshot_*.png in project root.
Add headless mode in scraper/driver_manager.py:options.add_argument("--headless")


Test CAPTCHA URL in browser.


Dynamic Dropdowns:
Ensure state selection updates district/court dropdowns.
Check browser console (F12) for JavaScript errors.


Database/Connection Issues:
Run as admin:python app.py --web --port 8000


Verify ChromeDriver path and version.


Directory Structure:
Confirm all folders/files exist:dir E:\ecourt_scraper /s

Notes

Dynamic Dropdowns: Includes all 28 states, 8 UTs, major districts, and all 25 High Courts plus key district courts.
CAPTCHA: Displays on first load and persists across submissions. Manual entry is default; 2Captcha is optional.
Limitations: Some CNRs (e.g., GJHC240000012025) may fail due to invalid data. Test with valid CNRs from https://services.ecourts.gov.in.

