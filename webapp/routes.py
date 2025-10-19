from flask import request, render_template, send_file, jsonify
from scraper.driver_manager import get_driver
from scraper.case_details import get_case_details
from scraper.captcha_solver import get_captcha_image, refresh_captcha
from utils.logger import logger
import os
import argparse
from app import run_scraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Full list of states and UTs for courts in India
STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat", "Haryana", 
    "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", 
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", 
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu", "Delhi", 
    "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
]

# Comprehensive districts by state (major districts; full list ~700+)
DISTRICTS = {
    "Andhra Pradesh": ["Anantapur", "Chittoor", "East Godavari", "Guntur", "Krishna", "Kurnool", "Visakhapatnam", "Vizianagaram", "West Godavari"],
    "Arunachal Pradesh": ["Changlang", "Dibang Valley", "East Kameng", "East Siang", "Lohit", "Lower Dibang Valley", "Lower Subansiri", "Papum Pare", "Tawang", "Tirap"],
    "Assam": ["Baksa", "Barpeta", "Bongaigaon", "Cachar", "Chirang", "Darrang", "Dhemaji", "Dhubri", "Dibrugarh", "Goalpara", "Golaghat", "Hailakandi", "Jorhat", "Kamrup", "Karbi Anglong", "Karimganj", "Kokrajhar", "Lakhimpur", "Morigaon", "Nagaon", "Nalbari", "Sibsagar", "Sonitpur", "Tinsukia", "Udalguri"],
    "Bihar": ["Araria", "Arwal", "Aurangabad", "Banka", "Begusarai", "Bhagalpur", "Bhojpur", "Buxar", "Darbhanga", "East Champaran", "Gaya", "Gopalganj", "Jamui", "Jehanabad", "Kaimur", "Katihar", "Khagaria", "Kishanganj", "Lakhisarai", "Madhepura", "Madhubani", "Munger", "Muzaffarpur", "Nalanda", "Nawada", "Patna", "Purnia", "Rohtas", "Saharsa", "Samastipur", "Saran", "Sheikhpura", "Sheohar", "Sitamarhi", "Siwan", "Supaul", "Vaishali", "West Champaran"],
    "Chhattisgarh": ["Balod", "Baloda Bazar", "Balrampur", "Bastar", "Bemetara", "Bijapur", "Bilaspur", "Dantewada", "Dhamtari", "Durg", "Gariaband", "Janjgir-Champa", "Jashpur", "Kabirdham", "Kanker", "Khairagarh-Chhuikhadan-Gandai", "Kondagaon", "Korba", "Korea", "Mahasamund", "Mungeli", "Narayanpur", "Raigarh", "Raipur", "Rajnandgaon", "Sukma", "Surajpur", "Surguja"],
    "Goa": ["North Goa", "South Goa"],
    "Gujarat": ["Ahmedabad", "Amreli", "Anand", "Aravalli", "Banaskantha", "Bharuch", "Bhavnagar", "Botad", "Chhota Udaipur", "Dahod", "Dang", "Devbhoomi Dwarka", "Gandhinagar", "Gir Somnath", "Jamnagar", "Junagadh", "Kachchh", "Kheda", "Mahisagar", "Mehsana", "Morbi", "Narmada", "Navsari", "Panchmahal", "Patan", "Porbandar", "Rajkot", "Sabarkantha", "Surat", "Surendranagar", "Tapi", "Vadodara", "Valsad"],
    "Haryana": ["Ambala", "Bhiwani", "Charkhi Dadri", "Faridabad", "Fatehabad", "Gurugram", "Hisar", "Jhajjar", "Jind", "Kaithal", "Karnal", "Kurukshetra", "Mahendragarh", "Nuh", "Palwal", "Panchkula", "Panipat", "Rewari", "Rohtak", "Sirsa", "Sonipat", "Yamunanagar"],
    "Himachal Pradesh": ["Bilaspur", "Chamba", "Hamirpur", "Kangra", "Kinnaur", "Kullu", "Lahaul and Spiti", "Mandi", "Shimla", "Sirmaur", "Solan", "Una"],
    "Jharkhand": ["Bokaro", "Chatra", "Deoghar", "Dhanbad", "Dumka", "East Singhbhum", "Garhwa", "Giridih", "Godda", "Gumla", "Hazaribagh", "Jamtara", "Khunti", "Koderma", "Latehar", "Lohardaga", "Pakur", "Palamu", "Ramgarh", "Ranchi", "Sahibganj", "Seraikela-Kharsawan", "Simdega", "West Singhbhum"],
    "Karnataka": ["Bagalkot", "Ballari", "Belagavi", "Bengaluru Rural", "Bengaluru Urban", "Bidar", "Chamarajanagar", "Chikkaballapur", "Chikkamagaluru", "Chitradurga", "Dakshina Kannada", "Davangere", "Dharwad", "Dharmapuri", "Gadag", "Hassan", "Haveri", "Kalaburagi", "Kodagu", "Kolar", "Koppal", "Mandya", "Mysuru", "Raichur", "Ramanagara", "Shivamogga", "Tumakuru", "Udupi", "Uttara Kannada", "Vijayapura", "Yadgir"],
    "Kerala": ["Alappuzha", "Ernakulam", "Idukki", "Kannur", "Kasaragod", "Kollam", "Kottayam", "Kozhikode", "Malappuram", "Palakkad", "Pathanamthitta", "Thiruvananthapuram", "Thrissur", "Wayanad"],
    "Madhya Pradesh": ["Agar Malwa", "Alirajpur", "Anuppur", "Ashoknagar", "Balaghat", "Barwani", "Betul", "Bhind", "Bhopal", "Burhanpur", "Chhindwara", "Damoh", "Datia", "Dewas", "Dhar", "Dindori", "Guna", "Gwalior", "Harda", "Hoshangabad", "Indore", "Jabalpur", "Jhabua", "Katni", "Khandwa", "Khargone", "Mandla", "Mandsaur", "Morena", "Narmadapuram", "Neemuch", "Niwari", "Panna", "Raisen", "Rajgarh", "Ratlam", "Rewa", "Sagar", "Satna", "Sehore", "Seoni", "Shahdol", "Shajapur", "Sheopur", "Shivpuri", "Sidhi", "Singrauli", "Tikamgarh", "Ujjain", "Umaria", "Vidisha"],
    "Maharashtra": ["Ahmednagar", "Akola", "Amravati", "Aurangabad", "Beed", "Bhandara", "Buldhana", "Chandrapur", "Dhule", "Gadchiroli", "Gondia", "Hingoli", "Jalgaon", "Jalna", "Kolhapur", "Latur", "Mumbai City", "Mumbai Suburban", "Nagpur", "Nanded", "Nandurbar", "Nashik", "Osmanabad", "Palghar", "Parbhani", "Pune", "Raigad", "Ratnagiri", "Sangli", "Satara", "Sindhudurg", "Solapur", "Thane", "Wardha", "Washim", "Yavatmal"],
    "Manipur": ["Bishnupur", "Chandel", "Churachandpur", "Imphal East", "Imphal West", "Kamjong", "Kangpokpi", "Kakching", "Kakching", "Kamle", "Kangpokpi", "Karaoke", "Kumbi", "Noney", "Pherzawl", "Senapati", "Tamenglong", "Tengnoupal", "Thoubal", "Ukhrul"],
    "Meghalaya": ["East Garo Hills", "East Khasi Hills", "East Jaintia Hills", "North Garo Hills", "Ri-Bhoi", "South Garo Hills", "South West Garo Hills", "South West Khasi Hills", "West Garo Hills", "West Jaintia Hills", "West Khasi Hills"],
    "Mizoram": ["Aizawl", "Champhai", "Hnahthial", "Khawzawl", "Kolasib", "Lawngtlai", "Lunglei", "Mamit", "Saiha", "Saitual", "Serchhip"],
    "Nagaland": ["Dimapur", "Kiphire", "Kohima", "Longleng", "Mokokchung", "Mon", "Peren", "Phek", "Tuensang", "Wokha", "Zunheboto"],
    "Odisha": ["Angul", "Balangir", "Balasore", "Bargarh", "Bhadrak", "Boudh", "Cuttack", "Deogarh", "Dhenkanal", "Gajapati", "Ganjam", "Jagatsinghpur", "Jajpur", "Jharsuguda", "Kalahandi", "Kandhamal", "Kendrapara", "Kendujhar", "Khordha", "Koraput", "Malkangiri", "Mayurbhanj", "Nabarangpur", "Nayagarh", "Nuapada", "Puri", "Rayagada", "Sambalpur", "Subarnapur", "Sundargarh"],
    "Punjab": ["Amritsar", "Barnala", "Bathinda", "Faridkot", "Fatehgarh Sahib", "Fazilka", "Ferozepur", "Gurdaspur", "Hoshiarpur", "Jalandhar", "Kapurthala", "Ludhiana", "Malerkotla", "Mansa", "Moga", "Pathankot", "Patiala", "Rupnagar", "Sahibzada Ajit Singh Nagar", "Sangrur", "Sri Muktsar Sahib", "Tarn Taran"],
    "Rajasthan": ["Ajmer", "Alwar", "Banswara", "Baran", "Barmer", "Bharatpur", "Bhilwara", "Bikaner", "Bundi", "Chittorgarh", "Churu", "Dausa", "Dholpur", "Dungarpur", "Hanumangarh", "Jaipur", "Jaisalmer", "Jalor", "Jhalawar", "Jhunjhunu", "Jodhpur", "Karauli", "Kota", "Nagaur", "Pali", "Pratapgarh", "Rajsamand", "Sawai Madhopur", "Sikar", "Sirohi", "Sri Ganganagar", "Tonk", "Udaipur"],
    "Sikkim": ["East Sikkim", "North Sikkim", "South Sikkim", "West Sikkim"],
    "Tamil Nadu": ["Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore", "Dharmapuri", "Dindigul", "Erode", "Kallakurichi", "Kanchipuram", "Kanyakumari", "Karur", "Krishnagiri", "Madurai", "Mayiladuthurai", "Nagapattinam", "Namakkal", "Nilgiris", "Perambalur", "Pudukkottai", "Ramanathapuram", "Ranipet", "Salem", "Sivaganga", "Tenkasi", "Thanjavur", "Theni", "Thoothukudi", "Tiruchirappalli", "Tirunelveli", "Tirupattur", "Tiruppur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur", "Vellore", "Viluppuram", "Virudhunagar"],
    "Telangana": ["Adilabad", "Bhadradri Kothagudem", "Hyderabad", "Jagtial", "Jangaon", "Jayashankar Bhupalpally", "Jogulamba Gadwal", "Kamareddy", "Karimnagar", "Khammam", "Komaram Bheem Asifabad", "Mahabubabad", "Mahabubnagar", "Mancherial", "Medak", "Medchal-Malkajgiri", "Mulugu", "Nagarkurnool", "Nalgonda", "Narayanpet", "Nirmal", "Nizamabad", "Peddapalli", "Rajanna Sircilla", "Ranga Reddy", "Sangareddy", "Siddipet", "Suryapet", "Vikarabad", "Wanaparthy", "Warangal (Rural)", "Warangal (Urban)", "Yadadri Bhuvanagiri"],
    "Tripura": ["Dhalai", "Gomati", "Khowai", "North Tripura", "Sepahijala", "South Tripura", "Unakoti", "West Tripura"],
    "Uttar Pradesh": ["Agra", "Aligarh", "Ambedkar Nagar", "Amethi", "Amroha", "Auraiya", "Ayodhya", "Azamgarh", "Baghpat", "Bahraich", "Ballia", "Balrampur", "Banda", "Barabanki", "Bareilly", "Basti", "Bhadohi", "Bijnor", "Budaun", "Bulandshahr", "Chandauli", "Chitrakoot", "Deoria", "Etah", "Etawah", "Farrukhabad", "Fatehpur", "Firozabad", "Gautam Buddha Nagar", "Ghaziabad", "Ghazipur", "Gonda", "Gorakhpur", "Hamirpur", "Hapur", "Hardoi", "Hathras", "Jalaun", "Jaunpur", "Jhansi", "Kannauj", "Kanpur Dehat", "Kanpur Nagar", "Kasganj", "Kaushambi", "Kheri", "Kushinagar", "Lalitpur", "Lucknow", "Maharajganj", "Mahoba", "Mainpuri", "Mathura", "Mau", "Meerut", "Mirzapur", "Moradabad", "Muzaffarnagar", "Pilibhit", "Pratapgarh", "Prayagraj", "Raebareli", "Rampur", "Saharanpur", "Sambhal", "Sant Kabir Nagar", "Shahjahanpur", "Shamli", "Shravasti", "Siddharthnagar", "Sitapur", "Sonbhadra", "Sultanpur", "Unnao", "Varanasi"],
    "Uttarakhand": ["Almora", "Bageshwar", "Chamoli", "Champawat", "Dehradun", "Haridwar", "Nainital", "Pauri Garhwal", "Pithoragarh", "Rudraprayag", "Tehri Garhwal", "Udham Singh Nagar", "Uttarkashi"],
    "West Bengal": ["Alipurduar", "Bankura", "Birbhum", "Cooch Behar", "Dakshin Dinajpur", "Darjeeling", "Hooghly", "Howrah", "Jalpaiguri", "Jhargram", "Kalimpong", "Kolkata", "Malda", "Murshidabad", "Nadia", "North 24 Parganas", "Paschim Bardhaman", "Paschim Medinipur", "Purba Bardhaman", "Purba Medinipur", "Purulia", "South 24 Parganas", "Uttar Dinajpur"],
    "Andaman and Nicobar Islands": ["Nicobar", "North and Middle Andaman", "South Andaman"],
    "Chandigarh": ["Chandigarh"],
    "Dadra and Nagar Haveli and Daman and Diu": ["Dadra and Nagar Haveli", "Daman", "Diu"],
    "Delhi": ["Central Delhi", "East Delhi", "New Delhi", "North Delhi", "North East Delhi", "North West Delhi", "Shahdara", "South Delhi", "South East Delhi", "South West Delhi", "West Delhi"],
    "Jammu and Kashmir": ["Anantnag", "Bandipora", "Baramulla", "Budgam", "Doda", "Ganderbal", "Jammu", "Kathua", "Kishtwar", "Kulgam", "Kupwara", "Poonch", "Pulwama", "Rajouri", "Ramban", "Reasi", "Samba", "Shopian", "Srinagar", "Udhampur"],
    "Ladakh": ["Kargil", "Leh"],
    "Lakshadweep": ["Lakshadweep"],
    "Puducherry": ["Karaikal", "Mahe", "Puducherry", "Yanam"]
}

# All 25 High Courts and key district courts
COURTS = {
    "Andhra Pradesh": ["Andhra Pradesh High Court", "District Court - Visakhapatnam"],
    "Arunachal Pradesh": ["Gauhati High Court (for Arunachal Pradesh)", "District Court - Itanagar"],
    "Assam": ["Gauhati High Court", "District Court - Guwahati"],
    "Bihar": ["Patna High Court", "District Court - Patna"],
    "Chhattisgarh": ["Chhattisgarh High Court", "District Court - Raipur"],
    "Goa": ["Bombay High Court (for Goa)", "District Court - Panaji"],
    "Gujarat": ["Gujarat High Court", "District Court - Ahmedabad"],
    "Haryana": ["Punjab and Haryana High Court", "District Court - Chandigarh"],
    "Himachal Pradesh": ["Himachal Pradesh High Court", "District Court - Shimla"],
    "Jharkhand": ["Jharkhand High Court", "District Court - Ranchi"],
    "Karnataka": ["Karnataka High Court", "District Court - Bengaluru"],
    "Kerala": ["Kerala High Court", "District Court - Ernakulam"],
    "Madhya Pradesh": ["Madhya Pradesh High Court", "District Court - Bhopal"],
    "Maharashtra": ["Bombay High Court", "District Court - Mumbai"],
    "Manipur": ["Manipur High Court", "District Court - Imphal"],
    "Meghalaya": ["Meghalaya High Court", "District Court - Shillong"],
    "Mizoram": ["Gauhati High Court (for Mizoram)", "District Court - Aizawl"],
    "Nagaland": ["Gauhati High Court (for Nagaland)", "District Court - Kohima"],
    "Odisha": ["Orissa High Court", "District Court - Cuttack"],
    "Punjab": ["Punjab and Haryana High Court", "District Court - Chandigarh"],
    "Rajasthan": ["Rajasthan High Court", "District Court - Jodhpur"],
    "Sikkim": ["Sikkim High Court", "District Court - Gangtok"],
    "Tamil Nadu": ["Madras High Court", "District Court - Chennai"],
    "Telangana": ["Telangana High Court", "District Court - Hyderabad"],
    "Tripura": ["Tripura High Court", "District Court - Agartala"],
    "Uttar Pradesh": ["Allahabad High Court", "District Court - Lucknow"],
    "Uttarakhand": ["Uttarakhand High Court", "District Court - Nainital"],
    "West Bengal": ["Calcutta High Court", "District Court - Kolkata"],
    "Andaman and Nicobar Islands": ["Calcutta High Court (for Andaman)", "District Court - Port Blair"],
    "Chandigarh": ["Punjab and Haryana High Court", "District Court - Chandigarh"],
    "Dadra and Nagar Haveli and Daman and Diu": ["Bombay High Court (for DNH)", "District Court - Daman"],
    "Delhi": ["Delhi High Court", "District Court - Tis Hazari"],
    "Jammu and Kashmir": ["Jammu and Kashmir and Ladakh High Court", "District Court - Srinagar"],
    "Ladakh": ["Jammu and Kashmir and Ladakh High Court", "District Court - Leh"],
    "Lakshadweep": ["Kerala High Court (for Lakshadweep)", "District Court - Kavaratti"],
    "Puducherry": ["Madras High Court (for Puducherry)", "District Court - Puducherry"]
}

def init_routes(app):
    @app.route('/', methods=['GET', 'POST'])
    def index():
        captcha_url = None
        driver = None
        try:
            driver = get_driver()
            driver.get("https://services.ecourts.gov.in/ecourtindia_v6/")
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            captcha_url, captcha_error = get_captcha_image(driver)
            if captcha_error:
                logger.error(f"Failed to get CAPTCHA image: {captcha_error}")
                return render_template('index.html', error=captcha_error, captcha_url=None, states=STATES)
        except Exception as e:
            logger.error(f"Error fetching initial CAPTCHA: {e}")
            return render_template('index.html', error=f"Error loading CAPTCHA: {e}", captcha_url=None, states=STATES)
        finally:
            if driver:
                driver.quit()

        if request.method == 'POST':
            logger.info("Received POST request")
            form_data = request.form.to_dict()
            for key in ['today', 'tomorrow', 'causelist', 'download_pdf']:
                form_data[key] = key in form_data
            captcha_code = form_data.get('captcha_code', None)
            form_data['captcha_code'] = captcha_code

            # Server-side validation
            errors = []
            if not form_data.get('cnr') and not (form_data.get('case_type') and form_data.get('case_number') and form_data.get('year')):
                errors.append("Provide CNR or Case Type/Number/Year")
            if not form_data.get('state') or form_data.get('state') not in STATES:
                errors.append("Invalid state")
            if form_data.get('state') != "Other" and (not form_data.get('district') or form_data.get('district') not in DISTRICTS.get(form_data.get('state'), [])):
                errors.append("Invalid district")
            if form_data.get('state') != "Other" and (not form_data.get('court') or form_data.get('court') not in COURTS.get(form_data.get('state'), [])):
                errors.append("Invalid court")
            if not form_data.get('captcha_code'):
                errors.append("CAPTCHA code required")

            if errors:
                return render_template('index.html', error="\n".join(errors), captcha_url=captcha_url, states=STATES)

            form_args = argparse.Namespace(**form_data)
            driver = get_driver(download_dir=os.path.abspath("downloads"))
            try:
                results, _ = run_scraper(form_args, driver)
                return render_template('index.html', results=results['output'], errors=results['errors'], captcha_url=captcha_url, states=STATES)
            except Exception as e:
                logger.error(f"Scraping error: {e}")
                return render_template('index.html', error=f"Scraping error: {e}", captcha_url=captcha_url, states=STATES)
            finally:
                driver.quit()

        return render_template('index.html', captcha_url=captcha_url, states=STATES)

    @app.route('/refresh_captcha', methods=['POST'])
    def refresh_captcha_route():
        try:
            driver = get_driver()
            try:
                driver.get("https://services.ecourts.gov.in/ecourtindia_v6/")
                WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                captcha_url, captcha_error = refresh_captcha(driver)
                if captcha_error:
                    return render_template('index.html', error=captcha_error, captcha_url=None, states=STATES)
                return render_template('index.html', captcha_url=captcha_url, states=STATES)
            finally:
                driver.quit()
        except Exception as e:
            logger.error(f"Error refreshing CAPTCHA: {e}")
            return render_template('index.html', error=f"Error refreshing CAPTCHA: {e}", captcha_url=None, states=STATES)

    @app.route('/get_districts/<state>', methods=['GET'])
    def get_districts(state):
        return jsonify(DISTRICTS.get(state, []))

    @app.route('/get_courts/<state>', methods=['GET'])
    def get_courts(state):
        return jsonify(COURTS.get(state, []))

    @app.route('/favicon.ico')
    def favicon():
        return send_file('static/favicon.ico', mimetype='image/x-icon') if os.path.exists('static/favicon.ico') else ('', 204)