
from datetime import datetime, timedelta

def get_date_str(shift=0):
    date = datetime.now() + timedelta(days=shift)
    return date.strftime('%d-%m-%Y')
