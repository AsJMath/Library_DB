from datetime import datetime, timedelta

def add_date(original_date, increment):
    new_date_obj = datetime.strptime(original_date, "%Y-%m-%d") + timedelta(days=increment)
    return new_date_obj.strftime("%Y-%m-%d")

def is_late(date1, date2):
    # returns number of days date2 is after date1, or 0 if date2 is not after date1
    if datetime.strptime(date2, "%Y-%m-%d") > datetime.strptime(date1, "%Y-%m-%d"):
        return (datetime.strptime(date2, "%Y-%m-%d") - datetime.strptime(date1, "%Y-%m-%d")).days
    else:
        return 0